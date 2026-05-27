"""Thin Gemini wrapper.

Three modes:
- STUB: neither GEMINI_API_KEY nor Vertex AI is configured. Returns a
  deterministic offline response so the full pipeline runs offline / in CI.
- API-KEY: GEMINI_API_KEY set. Calls Gemini Developer API via google-genai.
- VERTEX: GOOGLE_GENAI_USE_VERTEXAI=true. Calls Gemini on Vertex AI using
  Application Default Credentials (no API key — required where the Cloud
  security policy disallows API keys).
"""
from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass
class GeminiResult:
    text: str
    model: str
    prompt_tokens: int
    candidates_tokens: int
    total_tokens: int
    finish_reason: str | None
    response_id: str | None
    temperature: float
    is_stub: bool


class GeminiClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        vertex_ai: bool = False,
        project: str = "",
        location: str = "",
    ):
        self.api_key = api_key or ""
        self.model = model
        self.vertex_ai = bool(vertex_ai)
        self.project = project or ""
        self.location = location or ""

    @property
    def stub(self) -> bool:
        return not (self.api_key or self.vertex_ai)

    @property
    def mode(self) -> str:
        if self.stub:
            return "stub"
        if self.vertex_ai:
            return "vertex"
        return "api-key"

    def generate(self, prompt: str, temperature: float = 0.2) -> GeminiResult:
        if self.stub:
            return self._stub(prompt, temperature)
        return self._live(prompt, temperature)

    def _stub(self, prompt: str, temperature: float) -> GeminiResult:
        briefing = {
            "period": "see-input",
            "summary": (
                "[STUB OUTPUT] This is a deterministic offline response generated "
                "because neither GEMINI_API_KEY nor Vertex AI mode is enabled. The "
                "full pipeline (context injection, redaction, logging, dashboard) "
                "is exercised; only the language model call is stubbed."
            ),
            "notable_changes": [],
            "watch_items": [
                "Enable Vertex AI (GOOGLE_GENAI_USE_VERTEXAI=true) or set "
                "GEMINI_API_KEY to get a real plain-language briefing."
            ],
            "caveats": [
                "Explanatory only; not a certified audit.",
                "Generated in STUB mode (no live Gemini call).",
            ],
        }
        text = json.dumps(briefing, ensure_ascii=False)
        pt = max(1, len(prompt) // 4)
        ct = max(1, len(text) // 4)
        return GeminiResult(
            text=text,
            model=self.model,
            prompt_tokens=pt,
            candidates_tokens=ct,
            total_tokens=pt + ct,
            finish_reason="STOP",
            response_id="stub",
            temperature=temperature,
            is_stub=True,
        )

    def _live(self, prompt: str, temperature: float) -> GeminiResult:
        from google import genai  # lazy import; only needed for real calls

        if self.vertex_ai:
            # Vertex AI via Application Default Credentials. The google-genai SDK
            # reads GOOGLE_GENAI_USE_VERTEXAI / GOOGLE_CLOUD_PROJECT /
            # GOOGLE_CLOUD_LOCATION from the environment. No API key is used.
            client = genai.Client()
        else:
            client = genai.Client(api_key=self.api_key)

        resp = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={"temperature": temperature, "response_mime_type": "application/json"},
        )
        u = getattr(resp, "usage_metadata", None)
        fr = None
        try:
            fr = str(resp.candidates[0].finish_reason) if resp.candidates else None
        except Exception:  # noqa: BLE001
            fr = None
        return GeminiResult(
            text=resp.text or "",
            model=self.model,
            prompt_tokens=int(getattr(u, "prompt_token_count", 0) or 0),
            candidates_tokens=int(getattr(u, "candidates_token_count", 0) or 0),
            total_tokens=int(getattr(u, "total_token_count", 0) or 0),
            finish_reason=fr,
            response_id=getattr(resp, "response_id", None),
            temperature=temperature,
            is_stub=False,
        )
