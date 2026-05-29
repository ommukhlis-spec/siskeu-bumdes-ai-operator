"""Agent 4 - Monthly Report Explanation Assistant.

Flow:
load LynkMesh context -> fetch or receive synthetic/redacted report -> redact
-> build prompt -> call Gemini (real or stub) -> parse JSON/text -> write artifacts
-> ALWAYS log.

Debug helpers:
- GEMINI_FORCE_MINIMAL=1
  Forces the Gemini prompt to a tiny known-good prompt. Use this to prove
  the FastAPI endpoint can call live Gemini through the same GeminiClient.

- REPORT_EXPLAINER_DEBUG=1
  Prints agent-level debug information before calling Gemini.
"""
from __future__ import annotations

import json
import os
import time
from typing import Any

from app.agents.base import Agent
from app.evidence.run_logger import RunLogger
from app.evidence.schema import GeminiUsage
from app.gemini.prompts.registry import get_prompt
from app.siskeu.redact import redact_report



def _strip_json_fence(text: str | None) -> str:
    """Strip markdown JSON fences like ```json ... ``` before json.loads."""
    cleaned = (text or "").strip()
    fence = "`" * 3

    if cleaned.startswith(fence):
        lines = cleaned.splitlines()
        if len(lines) >= 2 and lines[-1].strip() == fence:
            first = lines[0].strip().lower()
            if first in {fence, fence + "json"}:
                return "\n".join(lines[1:-1]).strip()

    return cleaned


def _truthy(v: str | None) -> bool:
    return str(v or "").strip().lower() in {"1", "true", "yes", "y", "on"}


class ReportExplainerAgent(Agent):
    name = "report_explainer"
    version = "1.1.1"

    def __init__(self, *, config, logger, context_loader, gemini, report_source):
        self.config = config
        self.logger = logger
        self.context_loader = context_loader
        self.gemini = gemini
        self.report_source = report_source

    def _assemble_prompt(
        self,
        system_text: str,
        context_block: str,
        redacted_report: dict[str, Any],
        period: str,
    ) -> str:
        """Build the normal report-explanation prompt.

        Kept intentionally plain-text at API level. The prompt can request a
        JSON-like answer, but we do not rely on API-level JSON mode.
        """
        return (
            f"{system_text}\n\n"
            f"{context_block}\n\n"
            f"## Report data\n"
            f"Classification: {redacted_report.get('data_classification')}\n"
            f"{json.dumps(redacted_report, ensure_ascii=False, indent=2)}\n\n"
            "## Task\n"
            f"Explain the monthly report for period {period} in simple Indonesian.\n\n"
            "Return a concise response with these sections:\n"
            "1. Summary\n"
            "2. Notable changes\n"
            "3. Watch items\n"
            "4. Caveats\n\n"
            "Rules:\n"
            "- Use only figures present in the report data.\n"
            "- Do not invent numbers.\n"
            "- Do not claim this is a certified audit.\n"
            "- Do not post ledger entries.\n"
            "- Human review is required before final use.\n"
        )

    def run(self, tenant_ref_input: str, period: str):
        report = self.report_source.get_monthly_report(tenant_ref_input, period)
        return self.run_with_report(
            tenant_ref_input=tenant_ref_input,
            period=period,
            report=report,
            input_summary=f"Explain {period} monthly report from configured report source",
        )

    def run_with_report(
        self,
        *,
        tenant_ref_input: str,
        period: str,
        report: dict[str, Any],
        input_summary: str | None = None,
    ):
        """Run the explainer against an explicit report payload.

        This powers the interactive dashboard console. The payload should be
        synthetic or redacted unless a private production deployment is later
        implemented and evidenced.
        """
        run_id = RunLogger.new_run_id()
        system_text, prompt_ref = get_prompt("report_explanation", "v1")
        lm_ref = self.context_loader.lynkmesh_ref()

        log = self.logger.start_run(
            run_id=run_id,
            agent_name=self.name,
            agent_version=self.version,
            tenant_ref="pending",
            period=period,
            input_summary=input_summary or f"Explain {period} monthly report",
            lynkmesh=lm_ref,
            prompt=prompt_ref,
            data_classification=str(report.get("data_classification") or "synthetic"),
        )

        briefing = None

        try:
            redacted = redact_report(report)
            log.tenant_ref = redacted.get("tenant_ref", "unknown")
            log.data_classification = redacted.get("data_classification", "synthetic")

            full_prompt = self._assemble_prompt(
                system_text=system_text,
                context_block=self.context_loader.as_prompt_block(),
                redacted_report=redacted,
                period=period,
            )

            if _truthy(os.getenv("GEMINI_FORCE_MINIMAL", "")):
                full_prompt = "Say OK in one short sentence."

            if _truthy(os.getenv("REPORT_EXPLAINER_DEBUG", "")):
                print(
                    "[REPORT_EXPLAINER_DEBUG]",
                    {
                        "run_id": run_id,
                        "gemini_class": self.gemini.__class__.__name__,
                        "gemini_module": self.gemini.__class__.__module__,
                        "gemini_stub": getattr(self.gemini, "stub", None),
                        "gemini_vertex_enabled": getattr(self.gemini, "vertex_enabled", None),
                        "gemini_project": getattr(self.gemini, "google_cloud_project", None),
                        "gemini_location": getattr(self.gemini, "google_cloud_location", None),
                        "gemini_model": getattr(self.gemini, "model", None),
                        "force_minimal": _truthy(os.getenv("GEMINI_FORCE_MINIMAL", "")),
                        "prompt_len": len(full_prompt),
                        "prompt_preview": full_prompt[:300],
                    },
                    flush=True,
                )

            log.artifacts["prompt_ref"] = self.logger.write_artifact(
                run_id,
                "prompt.txt",
                full_prompt,
            )
            log.artifacts["redacted_report_ref"] = self.logger.write_artifact(
                run_id,
                "report_redacted.json",
                json.dumps(redacted, ensure_ascii=False, indent=2),
            )

            started = time.perf_counter()
            result = self.gemini.generate(full_prompt, temperature=0.2)
            elapsed_ms = int((time.perf_counter() - started) * 1000)

            latency_ms = int(getattr(result, "latency_ms", 0) or elapsed_ms or 1)

            log.artifacts["gemini_response_ref"] = self.logger.write_artifact(
                run_id,
                "response.txt",
                result.text,
            )

            log.gemini = GeminiUsage(
                model=result.model,
                response_id=result.response_id,
                finish_reason=result.finish_reason,
                prompt_tokens=result.prompt_tokens,
                candidates_tokens=result.candidates_tokens,
                total_tokens=result.total_tokens,
                latency_ms=latency_ms,
                temperature=0.2,
                is_stub=result.is_stub,
            )

            briefing = self._parse_briefing(result.text)
            log.result_status = "succeeded"

        except Exception as e:  # noqa: BLE001
            log.result_status = "failed"
            log.error = f"{type(e).__name__}: {e}"

        finally:
            self.logger.finalize(log)

        return log, briefing

    def _parse_briefing(self, text: str | None) -> dict[str, Any]:
        """Best-effort parser.

        The evidence run should succeed even if Gemini returns plain text.
        We store raw output when it is not JSON.
        """
        text = text or ""

        try:
            parsed = json.loads(_strip_json_fence(text))
            if isinstance(parsed, dict):
                parsed.setdefault("parse_error", False)
            if isinstance(parsed, dict):
                return parsed
            return {"raw": parsed, "parse_error": False}
        except Exception:  # noqa: BLE001
            return {
                "raw": text,
                "parse_error": True,
                "note": "Gemini returned plain text or non-JSON output. Raw response was stored.",
            }