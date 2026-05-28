"""Central configuration for Siskeu BUMDes AI Operator.

Rules:
- Gemini model is read from env, with safe fallback to gemini-2.5-flash.
- Vertex AI mode is enabled by either:
  - GEMINI_MODE=vertex
  - GOOGLE_GENAI_USE_VERTEXAI=true
- Vertex AI uses ADC/service account, no API key required.
- GOOGLE_CLOUD_PROJECT / GOOGLE_CLOUD_LOCATION are for Vertex Gemini.
- GCP_PROJECT is separate and only used for Firestore/store-related features.
- If neither Vertex mode nor API key is configured, the app uses stub mode.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def _abs(p: str) -> str:
    path = Path(p)
    return str(path if path.is_absolute() else (REPO_ROOT / path))


def _truthy(v: str | None) -> bool:
    return str(v or "").strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class Config:
    gemini_api_key: str
    gemini_model: str
    gemini_mode: str
    vertex_ai_enabled: bool
    google_cloud_project: str
    google_cloud_location: str

    gcp_project: str
    gcs_bucket: str
    firestore_collection_runs: str
    report_source: str
    report_fixture_dir: str
    lynkmesh_pack_path: str
    runs_dir: str
    app_env: str

    @property
    def stub_mode(self) -> bool:
        if self.vertex_ai_enabled and self.google_cloud_project:
            return False

        if self.gemini_api_key:
            return False

        return True

    @property
    def firestore_enabled(self) -> bool:
        return bool(self.gcp_project)


def load_config() -> Config:
    gemini_mode = os.getenv("GEMINI_MODE", "").strip().lower()

    google_cloud_project = (
        os.getenv("GOOGLE_CLOUD_PROJECT", "").strip()
        or os.getenv("GCP_PROJECT", "").strip()
    )

    google_cloud_location = (
        os.getenv("GOOGLE_CLOUD_LOCATION", "").strip()
        or "asia-southeast1"
    )

    vertex_ai_enabled = (
        gemini_mode == "vertex"
        or _truthy(os.getenv("GOOGLE_GENAI_USE_VERTEXAI", ""))
    )

    return Config(
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        gemini_model=os.getenv("GEMINI_MODEL", "").strip() or "gemini-2.5-flash",
        gemini_mode=gemini_mode,
        vertex_ai_enabled=vertex_ai_enabled,
        google_cloud_project=google_cloud_project,
        google_cloud_location=google_cloud_location,

        # Store / artifact config.
        # Keep this separate from GOOGLE_CLOUD_PROJECT so local Vertex AI usage
        # does not accidentally switch evidence storage to Firestore.
        gcp_project=os.getenv("GCP_PROJECT", "").strip(),
        gcs_bucket=os.getenv("GCS_BUCKET", "").strip(),
        firestore_collection_runs=os.getenv(
            "FIRESTORE_COLLECTION_RUNS",
            "agent_runs",
        ).strip(),
        report_source=os.getenv("REPORT_SOURCE", "synthetic").strip(),
        report_fixture_dir=_abs(os.getenv("REPORT_FIXTURE_DIR", "data/fixtures")),
        lynkmesh_pack_path=_abs(
            os.getenv(
                "LYNKMESH_PACK_PATH",
                "data/context_packs/sample_context_pack.json",
            )
        ),
        runs_dir=_abs(os.getenv("RUNS_DIR", "data/runs")),
        app_env=os.getenv("APP_ENV", "").strip(),
    )