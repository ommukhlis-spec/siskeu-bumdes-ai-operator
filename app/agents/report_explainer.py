"""Agent 4 - Monthly Report Explanation Assistant.

Flow: load LynkMesh context -> fetch synthetic report -> redact -> build prompt
-> call Gemini (real or stub) -> parse JSON -> write artifacts -> ALWAYS log.
"""
from __future__ import annotations

import json
import time

from app.agents.base import Agent
from app.evidence.run_logger import RunLogger
from app.evidence.schema import GeminiUsage
from app.gemini.prompts.registry import get_prompt
from app.siskeu.redact import redact_report


class ReportExplainerAgent(Agent):
    name = "report_explainer"
    version = "1.0.0"

    def __init__(self, *, config, logger, context_loader, gemini, report_source):
        self.config = config
        self.logger = logger
        self.context_loader = context_loader
        self.gemini = gemini
        self.report_source = report_source

    def _assemble_prompt(self, system_text, context_block, redacted_report, period) -> str:
        return (
            f"{system_text}\n\n"
            f"{context_block}\n\n"
            f"## Report data (REDACTED, classification: {redacted_report.get('data_classification')})\n"
            f"{json.dumps(redacted_report, ensure_ascii=False, indent=2)}\n\n"
            f"## Task\nProduce the JSON briefing for period {period}."
        )

    def run(self, tenant_ref_input: str, period: str):
        run_id = RunLogger.new_run_id()
        system_text, prompt_ref = get_prompt("report_explanation", "v1")
        lm_ref = self.context_loader.lynkmesh_ref()

        log = self.logger.start_run(
            run_id=run_id,
            agent_name=self.name,
            agent_version=self.version,
            tenant_ref="pending",
            period=period,
            input_summary=f"Explain {period} monthly report",
            lynkmesh=lm_ref,
            prompt=prompt_ref,
            data_classification="synthetic",
        )

        briefing = None
        try:
            report = self.report_source.get_monthly_report(tenant_ref_input, period)
            redacted = redact_report(report)
            log.tenant_ref = redacted.get("tenant_ref", "unknown")
            log.data_classification = redacted.get("data_classification", "synthetic")

            full_prompt = self._assemble_prompt(
                system_text, self.context_loader.as_prompt_block(), redacted, period
            )
            log.artifacts["prompt_ref"] = self.logger.write_artifact(run_id, "prompt.txt", full_prompt)
            log.artifacts["redacted_report_ref"] = self.logger.write_artifact(
                run_id, "report_redacted.json", json.dumps(redacted, ensure_ascii=False, indent=2)
            )

            t0 = time.time()
            result = self.gemini.generate(full_prompt)
            latency_ms = int((time.time() - t0) * 1000)

            log.artifacts["gemini_response_ref"] = self.logger.write_artifact(
                run_id, "response.json", result.text
            )
            log.gemini = GeminiUsage(
                model=result.model,
                response_id=result.response_id,
                finish_reason=result.finish_reason,
                prompt_tokens=result.prompt_tokens,
                candidates_tokens=result.candidates_tokens,
                total_tokens=result.total_tokens,
                latency_ms=latency_ms,
                temperature=result.temperature,
                is_stub=result.is_stub,
            )

            try:
                briefing = json.loads(result.text)
            except Exception:  # noqa: BLE001
                briefing = {"raw": result.text, "parse_error": True}

            log.result_status = "succeeded"
        except Exception as e:  # noqa: BLE001
            log.result_status = "failed"
            log.error = f"{type(e).__name__}: {e}"
        finally:
            self.logger.finalize(log)

        return log, briefing
