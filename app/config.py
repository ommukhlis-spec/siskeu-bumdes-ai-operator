"""Central configuration, loaded from environment variables.

Rules baked in:
- The Gemini model is ALWAYS read from env (never hardcoded).
- If neither GEMINI_API_KEY nor Vertex AI mode is enabled -> stub mode.
- Vertex AI mode is enabled when GOOGLE_GENAI_USE_VERTEXAI=true and uses
  Application Default Credentials (no API key needed). It reads
  GOOGLE_CLOUD_PROJECT / GOOGLE_CLOUD_LOCATION for the Vertex endpoint.
- Firestore is a SEPARATE concern: it is enabled ONLY when GCP_PROJECT is set.
  GOOGLE_CLOUD_PROJECT (used by Vertex) does NOT enable Firestore — running
  Vertex without GCP_PROJECT keeps evidence logging on local JSONL.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _abs(p: str) -> str:
    path = Path(p)
    return str(path if path.is_absolute() else (REPO_ROOT / path))


def _bool_env(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Config:
    gemini_api_key: str
    gemini_model: str
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
        return not (self.gemini_api_key or self.vertex_ai_enabled)

    @property
    def firestore_enabled(self) -> bool:
        return bool(self.gcp_project)


def load_config() -> Config:
    return Config(
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        gemini_model=os.getenv("GEMINI_MODEL", "").strip() or "stub-model",
        vertex_ai_enabled=_bool_env("GOOGLE_GENAI_USE_VERTEXAI"),
        google_cloud_project=os.getenv("GOOGLE_CLOUD_PROJECT", "").strip(),
        google_cloud_location=os.getenv("GOOGLE_CLOUD_LOCATION", "").strip(),
        gcp_project=os.getenv("GCP_PROJECT", "").strip(),
        gcs_bucket=os.getenv("GCS_BUCKET", "").strip(),
        firestore_collection_runs=os.getenv("FIRESTORE_COLLECTION_RUNS", "agent_runs").strip(),
        report_source=os.getenv("REPORT_SOURCE", "synthetic").strip(),
        report_fixture_dir=_abs(os.getenv("REPORT_FIXTURE_DIR", "data/fixtures")),
        lynkmesh_pack_path=_abs(
            os.getenv("LYNKMESH_PACK_PATH", "data/context_packs/sample_context_pack.json")
        ),
        runs_dir=_abs(os.getenv("RUNS_DIR", "data/runs")),
        app_env=os.getenv("APP_ENV", "").strip(),
    )
