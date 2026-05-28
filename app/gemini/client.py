"""Gemini wrapper for Siskeu BUMDes AI Operator.

Supports:
- Vertex AI + ADC/service account when GEMINI_MODE=vertex or GOOGLE_GENAI_USE_VERTEXAI=true
- API-key mode when GEMINI_API_KEY is set
- Deterministic STUB fallback for local/CI when no live credential is configured

Important:
- Default Vertex location is asia-southeast1 because gemini-2.5-flash was verified
  working there for this project.
- Do not force response_mime_type/application-json here. Some Vertex/Gemini
  project/region combinations can reject that with FAILED_PRECONDITION.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class GeminiResult:
    text: str
    model: str
    prompt_tokens: int
    candidates_tokens: int
    total_tokens: int
    finish_reason: str | None
    response_id: str | None
    is_stub: bool
    latency_ms: int


def _truthy(v: str | None) -> bool:
    return str(v or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _debug_enabled() -> bool:
    return _truthy(os.getenv("GEMINI_DEBUG", ""))


class GeminiClient:
    def __init__(self, api_key: str = "", model: str = ""):
        self.api_key = (api_key or os.getenv("GEMINI_API_KEY", "")).strip()
        self.model = (model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")).strip()

        self.gemini_mode = os.getenv("GEMINI_MODE", "").strip().lower()
        self.vertex_enabled = (
            self.gemini_mode == "vertex"
            or _truthy(os.getenv("GOOGLE_GENAI_USE_VERTEXAI", ""))
        )

        self.google_cloud_project = (
            os.getenv("GOOGLE_CLOUD_PROJECT", "").strip()
            or os.getenv("GCP_PROJECT", "").strip()
        )

        # IMPORTANT:
        # asia-southeast1 has been verified working with gemini-2.5-flash.
        # Do not default to asia-southeast2 for Gemini model calls.
        self.google_cloud_location = os.getenv(
            "GOOGLE_CLOUD_LOCATION",
            "asia-southeast1",
        ).strip() or "asia-southeast1"

    @property
    def stub(self) -> bool:
        """Return True only when neither Vertex mode nor API key mode is usable."""
        if self.vertex_enabled and self.google_cloud_project:
            return False

        if self.api_key:
            return False

        return True

    @property
    def effective_mode(self) -> str:
        """Resolved call path: stub | vertex | api_key."""
        if self.stub:
            return "stub"
        if self.vertex_enabled:
            return "vertex"
        return "api_key"

    def generate(self, prompt: str, temperature: float = 0.2) -> GeminiResult:
        prompt = prompt or ""

        if _debug_enabled():
            print(
                "[GEMINI_CLIENT_GENERATE_ENTER]",
                {
                    "module": __name__,
                    "file": __file__,
                    "mode": self.effective_mode,
                    "stub": self.stub,
                    "vertex_enabled": self.vertex_enabled,
                    "project": self.google_cloud_project,
                    "location": self.google_cloud_location,
                    "model": self.model,
                    "prompt_len": len(prompt),
                    "force_minimal": _truthy(os.getenv("GEMINI_FORCE_MINIMAL", "")),
                },
                flush=True,
            )

        if self.stub:
            return self._stub(prompt)

        if self.vertex_enabled:
            return self._live_vertex(prompt, temperature)

        return self._live_api_key(prompt, temperature)

    def _stub(self, prompt: str) -> GeminiResult:
        briefing = {
            "period": "see-input",
            "summary": (
                "[STUB OUTPUT] This deterministic offline response was generated "
                "because no live Gemini credential was configured. The pipeline "
                "is exercised, but the language model call is stubbed."
            ),
            "notable_changes": [],
            "watch_items": [
                "Use GEMINI_MODE=vertex with ADC/service account or set GEMINI_API_KEY for live Gemini."
            ],
            "caveats": [
                "Explanatory only; not a certified audit.",
                "Generated in STUB mode.",
            ],
        }

        text = json.dumps(briefing, ensure_ascii=False)
        prompt_tokens = max(1, len(prompt) // 4)
        candidates_tokens = max(1, len(text) // 4)

        return GeminiResult(
            text=text,
            model="stub-model",
            prompt_tokens=prompt_tokens,
            candidates_tokens=candidates_tokens,
            total_tokens=prompt_tokens + candidates_tokens,
            finish_reason="STOP",
            response_id="stub",
            is_stub=True,
            latency_ms=0,
        )

    def _live_vertex(self, prompt: str, temperature: float) -> GeminiResult:
        from google import genai
        from google.genai.types import HttpOptions

        started = time.perf_counter()

        if _debug_enabled():
            print(
                "[GEMINI_VERTEX_DEBUG]",
                {
                    "mode": "vertex",
                    "project": self.google_cloud_project,
                    "location": self.google_cloud_location,
                    "model": self.model,
                    "prompt_len": len(prompt),
                    "prompt_preview": prompt[:300],
                },
                flush=True,
            )

        client = genai.Client(
            vertexai=True,
            project=self.google_cloud_project,
            location=self.google_cloud_location,
            http_options=HttpOptions(api_version="v1"),
        )

        # Do not force response_mime_type here.
        # Basic Vertex call has already been verified working without JSON mode.
        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={
                "temperature": temperature,
            },
        )

        latency_ms = int((time.perf_counter() - started) * 1000)
        return self._to_result(response, is_stub=False, latency_ms=latency_ms)

    def _live_api_key(self, prompt: str, temperature: float) -> GeminiResult:
        from google import genai

        started = time.perf_counter()

        if _debug_enabled():
            print(
                "[GEMINI_API_KEY_DEBUG]",
                {
                    "mode": "api_key",
                    "model": self.model,
                    "prompt_len": len(prompt),
                    "prompt_preview": prompt[:300],
                },
                flush=True,
            )

        client = genai.Client(api_key=self.api_key)

        # Keep API-key path consistent with Vertex path:
        # no forced response_mime_type while stabilizing live evidence runs.
        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={
                "temperature": temperature,
            },
        )

        latency_ms = int((time.perf_counter() - started) * 1000)
        return self._to_result(response, is_stub=False, latency_ms=latency_ms)

    def _to_result(self, response: Any, *, is_stub: bool, latency_ms: int) -> GeminiResult:
        usage = getattr(response, "usage_metadata", None)

        prompt_tokens = int(getattr(usage, "prompt_token_count", 0) or 0)
        candidates_tokens = int(getattr(usage, "candidates_token_count", 0) or 0)
        total_tokens = int(getattr(usage, "total_token_count", 0) or 0)

        finish_reason = self._extract_finish_reason(response)
        text = self._extract_text(response)
        response_id = self._extract_response_id(response)

        return GeminiResult(
            text=text,
            model=self.model,
            prompt_tokens=prompt_tokens,
            candidates_tokens=candidates_tokens,
            total_tokens=total_tokens,
            finish_reason=finish_reason or "STOP",
            response_id=response_id,
            is_stub=is_stub,
            latency_ms=max(1, int(latency_ms or 0)),
        )

    def _extract_text(self, response: Any) -> str:
        try:
            text = getattr(response, "text", None)
            if text:
                return str(text)
        except Exception:
            pass

        try:
            candidates = getattr(response, "candidates", None) or []
            if not candidates:
                return ""

            content = getattr(candidates[0], "content", None)
            parts = getattr(content, "parts", None) if content else None
            if not parts:
                return ""

            chunks: list[str] = []
            for part in parts:
                part_text = getattr(part, "text", None)
                if part_text:
                    chunks.append(str(part_text))

            return "\n".join(chunks).strip()
        except Exception:
            return ""

    def _extract_finish_reason(self, response: Any) -> str | None:
        try:
            candidates = getattr(response, "candidates", None) or []
            if not candidates:
                return None

            finish_reason = getattr(candidates[0], "finish_reason", None)
            if finish_reason is None:
                return None

            # google-genai may return enum-like values.
            value = getattr(finish_reason, "value", None)
            if value:
                return str(value)

            name = getattr(finish_reason, "name", None)
            if name:
                return str(name)

            return str(finish_reason)
        except Exception:
            return None

    def _extract_response_id(self, response: Any) -> str | None:
        for attr in ("response_id", "id", "name"):
            try:
                value = getattr(response, attr, None)
                if value:
                    return str(value)
            except Exception:
                continue

        return None