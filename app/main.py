"""FastAPI entrypoint. Wires config -> store -> logger -> agent, exposes routes."""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.agents.report_explainer import ReportExplainerAgent
from app.config import load_config
from app.dashboard.routes import router as dashboard_router
from app.evidence.run_logger import RunLogger
from app.evidence.store import get_store
from app.gemini.client import GeminiClient
from app.lynkmesh.context_loader import ContextLoader
from app.siskeu.report_adapter import build_custom_synthetic_report, get_report_source


class RunRequest(BaseModel):
    tenant_ref: str = "synthetic-tenant-001"
    period: str = "2026-04"


class InteractiveRunRequest(BaseModel):
    """Synthetic/redacted report input from the interactive dashboard console."""

    tenant_ref: str = "synthetic-tenant-001"
    period: str = "2026-04"
    currency: str = "IDR"

    cash_beginning: int = 12_000_000
    cash_ending: int = 17_500_000
    revenue: int = 45_200_000
    cost_of_goods_sold: int = 21_500_000
    operating_expenses: int = 9_800_000
    prev_month_net_income: int = 11_200_000

    receivables: int = 7_200_000
    inventory: int = 12_400_000
    fixed_assets_net: int = 64_000_000
    payables: int = 5_400_000
    short_term_debt: int = 8_000_000
    village_capital: int = 95_000_000

    unit_air_bersih: int = 5_200_000
    unit_simpan_pinjam: int = 6_100_000
    unit_toko_desa: int = 2_600_000

    unposted_drafts: int = Field(default=1, ge=0)
    missing_opening_balance_accounts: int = Field(default=0, ge=0)
    notes: str = "Synthetic dashboard input for AI Operator demo."


class ReviewRequest(BaseModel):
    status: str
    reviewer_ref: str | None = None
    notes: str | None = None


def build_app() -> FastAPI:
    cfg = load_config()
    store = get_store(cfg)
    logger = RunLogger(store, cfg.runs_dir)
    context_loader = ContextLoader(cfg.lynkmesh_pack_path)
    gemini = GeminiClient(api_key=cfg.gemini_api_key, model=cfg.gemini_model)
    report_source = get_report_source(cfg)
    agent = ReportExplainerAgent(
        config=cfg,
        logger=logger,
        context_loader=context_loader,
        gemini=gemini,
        report_source=report_source,
    )

    app = FastAPI(title="Siskeu BUMDes AI Operator", version="1.1.0")
    app.state.store = store
    app.state.config = cfg
    app.state.agent = agent

    @app.get("/healthz")
    def healthz():
        return {
            "status": "ok",
            "stub_mode": cfg.stub_mode,
            "store": store.backend_name,
            "model": cfg.gemini_model,
        }

    @app.get("/version")
    def version():
        return {
            "app": "siskeu-bumdes-ai-operator",
            "version": "1.1.0-interactive-console",
            "stub_mode": cfg.stub_mode,
            "gemini_model": cfg.gemini_model,
            "report_source": cfg.report_source,
            "store": store.backend_name,
        }

    @app.get("/debug/gemini")
    def debug_gemini():
        """Safe, non-secret runtime info about the live GeminiClient in use.

        Never returns API keys, ADC contents, service-account JSON, or tokens.
        """
        client = app.state.agent.gemini
        client_module = type(client).__module__
        client_file = getattr(sys.modules.get(client_module), "__file__", None)
        return {
            "stub_mode": cfg.stub_mode,
            "gemini_model": cfg.gemini_model,
            "gemini_mode": client.effective_mode,
            "vertex_ai_enabled": cfg.vertex_ai_enabled,
            "google_cloud_project": cfg.google_cloud_project,
            "google_cloud_location": cfg.google_cloud_location,
            "gemini_client_module": client_module,
            "gemini_client_file": client_file,
            "gemini_client_stub": client.stub,
            "gemini_client_vertex_enabled": client.vertex_enabled,
            "store": store.backend_name,
        }

    @app.post("/debug/gemini/minimal-run")
    def debug_gemini_minimal_run():
        """Call the exact GeminiClient used by the dashboard with a tiny prompt.

        Proves the live path works without writing an ExecutionLog.
        """
        client = app.state.agent.gemini
        try:
            result = client.generate("Say OK in one short sentence.", 0.2)
            return {
                "ok": True,
                "model": result.model,
                "is_stub": result.is_stub,
                "prompt_tokens": result.prompt_tokens,
                "candidates_tokens": result.candidates_tokens,
                "total_tokens": result.total_tokens,
                "latency_ms": result.latency_ms,
                "response_id": result.response_id,
                "text": result.text,
            }
        except Exception as e:  # noqa: BLE001
            return JSONResponse(
                {
                    "ok": False,
                    "error_class": type(e).__name__,
                    "error_message": _sanitize_error(str(e)),
                },
                status_code=500,
            )

    @app.post("/agents/report-explanation/run")
    def run_report(req: RunRequest):
        log, briefing = agent.run(req.tenant_ref, req.period)
        return _run_response(log, briefing)

    @app.post("/agents/report-explanation/run-custom")
    def run_custom_report(req: InteractiveRunRequest):
        payload: dict[str, Any] = req.model_dump(mode="json")
        report = build_custom_synthetic_report(payload)
        log, briefing = agent.run_with_report(
            tenant_ref_input=req.tenant_ref,
            period=req.period,
            report=report,
            input_summary=f"Explain {req.period} monthly report from interactive synthetic dashboard input",
        )
        return _run_response(log, briefing, report_preview=report)

    @app.post("/runs/{run_id}/review")
    def review(run_id: str, req: ReviewRequest):
        if req.status not in {"pending", "approved", "rejected", "edited"}:
            return JSONResponse({"error": "status must be pending|approved|rejected|edited"}, status_code=400)
        review_doc = {
            "status": req.status,
            "reviewer_ref": req.reviewer_ref,
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
            "notes": req.notes,
        }
        updated = store.update_review(run_id, review_doc)
        if not updated:
            return JSONResponse({"error": "run not found"}, status_code=404)
        return {"run_id": run_id, "human_review": updated["human_review"]}

    app.include_router(dashboard_router)
    return app


def _sanitize_error(message: str, max_len: int = 600) -> str:
    """Collapse and truncate an error string for safe debug exposure.

    Vertex/genai errors do not normally embed secrets, but we still avoid
    leaking long bearer-token-like fragments and cap the length.
    """
    text = " ".join((message or "").split())
    redacted: list[str] = []
    for token in text.split(" "):
        if len(token) > 40 and any(c.isalnum() for c in token):
            redacted.append("[REDACTED]")
        else:
            redacted.append(token)
    cleaned = " ".join(redacted)
    return cleaned[:max_len]


def _run_response(log, briefing, report_preview: dict | None = None) -> dict:
    data = {
        "run_id": log.run_id,
        "result_status": log.result_status,
        "error": log.error,
        "human_review": log.human_review.model_dump(mode="json"),
        "lynkmesh_context_pack_id": log.lynkmesh.context_pack_id,
        "gemini": log.gemini.model_dump(mode="json") if log.gemini else None,
        "briefing": briefing,
    }
    if report_preview is not None:
        data["report_preview"] = {
            "period": report_preview.get("period"),
            "data_classification": report_preview.get("data_classification"),
            "income_statement": report_preview.get("income_statement"),
            "flags": report_preview.get("flags"),
        }
    return data


app = build_app()
