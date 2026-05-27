"""FastAPI entrypoint. Wires config -> store -> logger -> agent, exposes routes.

Health endpoints are registered BEFORE any heavy initialization so they remain
available even if a downstream subsystem misbehaves at startup. Multiple
equivalent health paths (/healthz, /health, /api/health, /livez, /readyz) exist
because some hosting layers intercept specific paths (e.g. /healthz) — having
alternates means at least one always reaches the app.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel

from app.agents.report_explainer import ReportExplainerAgent
from app.config import load_config
from app.dashboard.routes import router as dashboard_router
from app.evidence.run_logger import RunLogger
from app.evidence.store import get_store
from app.evidence.structured_cloud_logger import emit_human_review_updated
from app.gemini.client import GeminiClient
from app.lynkmesh.context_loader import ContextLoader
from app.siskeu.report_adapter import get_report_source


class RunRequest(BaseModel):
    tenant_ref: str = "synthetic-tenant-001"
    period: str = "2026-04"


class ReviewRequest(BaseModel):
    status: str
    reviewer_ref: str | None = None
    notes: str | None = None


app = FastAPI(title="Siskeu BUMDes AI Operator", version="1.0.0")


# ---------------------------------------------------------------------------
# Always-on, dependency-free routes. Registered FIRST.
# These do NOT touch app.state and must succeed even before init completes.
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "service": "siskeu-bumdes-ai-operator",
        "version": "1.0.0",
        "status": "ok",
        "docs": "/docs",
        "health": ["/healthz", "/health", "/api/health"],
    }


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/health")
def api_health():
    return {"status": "ok"}


@app.get("/livez", include_in_schema=False)
def livez():
    return PlainTextResponse("ok")


@app.get("/readyz", include_in_schema=False)
def readyz():
    return PlainTextResponse("ok")


# ---------------------------------------------------------------------------
# Heavy initialization (config + store + agent). Happens at import time so
# Cloud Run startup probe still sees a ready app, but the routes above are
# already attached regardless of what happens below.
# ---------------------------------------------------------------------------

cfg = load_config()
store = get_store(cfg)
run_logger = RunLogger(store, cfg.runs_dir)
context_loader = ContextLoader(cfg.lynkmesh_pack_path)
gemini = GeminiClient(
    api_key=cfg.gemini_api_key,
    model=cfg.gemini_model,
    vertex_ai=cfg.vertex_ai_enabled,
    project=cfg.google_cloud_project,
    location=cfg.google_cloud_location,
)
report_source = get_report_source(cfg)
agent = ReportExplainerAgent(
    config=cfg,
    logger=run_logger,
    context_loader=context_loader,
    gemini=gemini,
    report_source=report_source,
)

app.state.store = store
app.state.config = cfg


@app.get("/version")
def version():
    return {
        "service": "siskeu-bumdes-ai-operator",
        "version": "1.0.0",
        "stub_mode": cfg.stub_mode,
        "gemini_mode": gemini.mode,
        "store": store.backend_name,
        "model": cfg.gemini_model,
        "app_env": cfg.app_env,
    }


@app.post("/agents/report-explanation/run")
def run_report(req: RunRequest):
    log, briefing = agent.run(req.tenant_ref, req.period)
    return {
        "run_id": log.run_id,
        "result_status": log.result_status,
        "error": log.error,
        "human_review": log.human_review.model_dump(mode="json"),
        "lynkmesh_context_pack_id": log.lynkmesh.context_pack_id,
        "gemini": log.gemini.model_dump(mode="json") if log.gemini else None,
        "briefing": briefing,
    }


@app.post("/runs/{run_id}/review")
def review(run_id: str, req: ReviewRequest):
    review_doc = {
        "status": req.status,
        "reviewer_ref": req.reviewer_ref,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "notes": req.notes,
    }
    updated = store.update_review(run_id, review_doc)
    if not updated:
        return JSONResponse({"error": "run not found"}, status_code=404)
    emit_human_review_updated(run_id, updated.get("human_review", review_doc), updated)
    return {"run_id": run_id, "human_review": updated["human_review"]}


app.include_router(dashboard_router)
