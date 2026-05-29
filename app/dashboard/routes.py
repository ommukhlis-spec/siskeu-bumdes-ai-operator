"""Evidence-first dashboard + JSON APIs over the run store.

The dashboard is intentionally focused on XPRIZE proof points:
- deployed AI workflow status,
- Gemini live-vs-stub evidence,
- LynkMesh context grounding,
- ExecutionLog history,
- human review state.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))

REVIEWED_STATUSES = {"approved", "rejected", "edited"}


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or default)
    except (TypeError, ValueError):
        return default


def _short(value: Any, chars: int = 12) -> str:
    text = str(value or "")
    if not text:
        return "-"
    return text if len(text) <= chars else f"{text[:chars]}..."


def _gemini(run: dict[str, Any]) -> dict[str, Any]:
    return run.get("gemini") or {}


def _lynkmesh(run: dict[str, Any]) -> dict[str, Any]:
    return run.get("lynkmesh") or {}


def _human_review(run: dict[str, Any]) -> dict[str, Any]:
    return run.get("human_review") or {}


def _runtime_metadata(request: Request) -> dict[str, Any]:
    """Expose public-safe runtime details for the dashboard.

    Do not include secrets, env var values containing keys, service-account paths, or raw private paths.
    """
    cfg = getattr(request.app.state, "config", None)
    store = getattr(request.app.state, "store", None)

    def cfg_get(name: str, default: Any = None) -> Any:
        return getattr(cfg, name, default) if cfg is not None else default

    # Different project revisions used slightly different config field names.
    google_project = cfg_get("google_cloud_project", None) or cfg_get("gcp_project", None)
    google_location = cfg_get("google_cloud_location", None) or cfg_get("gcp_location", None)
    gemini_mode = cfg_get("gemini_mode", "vertex" if cfg_get("vertex_ai_enabled", False) else "api_or_stub")

    return {
        "service_name": "siskeu-bumdes-ai-operator",
        "cloud_run_region": "asia-southeast2",
        "store_backend": getattr(store, "backend_name", "unknown"),
        "stub_mode": bool(cfg_get("stub_mode", False)),
        "gemini_mode": gemini_mode,
        "vertex_ai_enabled": bool(cfg_get("vertex_ai_enabled", False)),
        "google_cloud_project": google_project or "configured in runtime",
        "google_cloud_location": google_location or "configured in runtime",
        "gemini_model": cfg_get("gemini_model", "configured in runtime"),
        "report_source": cfg_get("report_source", "synthetic"),
        "data_mode": "synthetic/redacted demo data",
        "safety_boundary": "AI explains, checks, and proposes. Humans approve final financial decisions.",
    }


def _summary(store) -> dict[str, Any]:
    runs = store.list_runs(limit=1000)
    reviewed = [r for r in runs if _human_review(r).get("status") in REVIEWED_STATUSES]
    approved = [r for r in reviewed if _human_review(r).get("status") == "approved"]
    failed = [r for r in runs if r.get("result_status") == "failed"]
    succeeded = [r for r in runs if r.get("result_status") == "succeeded"]

    live_runs = [r for r in runs if _gemini(r) and not bool(_gemini(r).get("is_stub"))]
    stub_runs = [r for r in runs if bool(_gemini(r).get("is_stub"))]
    total_tokens = sum(_as_int(_gemini(r).get("total_tokens")) for r in runs)
    context_packs = {_lynkmesh(r).get("context_pack_id") for r in runs if _lynkmesh(r).get("context_pack_id")}

    latest_run = runs[0] if runs else None
    latest_approved = approved[0] if approved else None
    latest_for_evidence = latest_approved or latest_run or {}
    latest_gemini = _gemini(latest_for_evidence)
    latest_lm = _lynkmesh(latest_for_evidence)
    latest_review = _human_review(latest_for_evidence)

    return {
        "total_runs": len(runs),
        "succeeded": len(succeeded),
        "failed": len(failed),
        "reviewed": len(reviewed),
        "approved": len(approved),
        "pending_review": sum(1 for r in runs if _human_review(r).get("status") == "pending"),
        "approval_rate": (len(approved) / len(reviewed)) if reviewed else None,
        "total_gemini_tokens": total_tokens,
        "distinct_context_packs": len(context_packs),
        "live_runs": len(live_runs),
        "stub_runs": len(stub_runs),
        "latest_run_id": latest_for_evidence.get("run_id"),
        "latest_run_id_short": _short(latest_for_evidence.get("run_id"), 8),
        "latest_created_at": latest_for_evidence.get("created_at"),
        "latest_completed_at": latest_for_evidence.get("completed_at"),
        "latest_result_status": latest_for_evidence.get("result_status"),
        "latest_human_review": latest_review.get("status"),
        "latest_model": latest_gemini.get("model"),
        "latest_is_stub": latest_gemini.get("is_stub"),
        "latest_total_tokens": latest_gemini.get("total_tokens"),
        "latest_latency_ms": latest_gemini.get("latency_ms"),
        "latest_context_pack_id": latest_lm.get("context_pack_id"),
        "latest_context_pack_id_short": _short(latest_lm.get("context_pack_id"), 16),
        "latest_graph_id": latest_lm.get("graph_id"),
        "latest_build_id": latest_lm.get("build_id"),
        "latest_generator_version": latest_lm.get("generator_version"),
        "latest_schema_version": latest_lm.get("schema_version"),
        "latest_token_estimate": latest_lm.get("token_estimate"),
    }


@router.get("/api/runs")
def api_runs(request: Request, limit: int = 100):
    return request.app.state.store.list_runs(limit=limit)


@router.get("/api/runs/{run_id}")
def api_run(request: Request, run_id: str):
    return request.app.state.store.get_run(run_id) or {"error": "not found"}


@router.get("/api/summary")
def api_summary(request: Request):
    return _summary(request.app.state.store)


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    store = request.app.state.store
    runs = store.list_runs(limit=100)
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "request": request,
            "runs": runs,
            "summary": _summary(store),
            "runtime": _runtime_metadata(request),
        },
    )
