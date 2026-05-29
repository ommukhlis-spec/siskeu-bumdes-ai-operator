"""Read-only dashboard + JSON APIs over the run store.

This module intentionally stays read-only for dashboard/API inspection.
AI execution and human review actions are handled by app.main.

Cloud Run compatibility note:
Use keyword arguments for Jinja2Templates.TemplateResponse().
Some Starlette/FastAPI versions interpret positional arguments differently:
    TemplateResponse("dashboard.html", {...})
can be interpreted as:
    request="dashboard.html", name={...}
which causes:
    TypeError: unhashable type: 'dict'

So we always call:
    templates.TemplateResponse(request=request, name="dashboard.html", context=context)
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


router = APIRouter()
templates = Jinja2Templates(
    directory=str(Path(__file__).resolve().parent / "templates")
)


def _as_int(value: Any, default: int = 0) -> int:
    """Best-effort int conversion for dashboard counters."""
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _review_status(run: dict[str, Any]) -> str:
    review = run.get("human_review") or {}
    return str(review.get("status") or "pending")


def _gemini(run: dict[str, Any]) -> dict[str, Any]:
    value = run.get("gemini") or {}
    return value if isinstance(value, dict) else {}


def _lynkmesh(run: dict[str, Any]) -> dict[str, Any]:
    value = run.get("lynkmesh") or {}
    return value if isinstance(value, dict) else {}


def _summary(store) -> dict[str, Any]:
    """Build evidence-oriented dashboard summary.

    Failed runs are counted, not hidden. This is intentional: the dashboard is
    an evidence viewer, not a marketing-only UI.
    """
    runs = store.list_runs(limit=1000)

    reviewed = [
        r
        for r in runs
        if _review_status(r) in {"approved", "rejected", "edited"}
    ]
    approved = [
        r
        for r in reviewed
        if _review_status(r) == "approved"
    ]

    total_tokens = sum(
        _as_int(_gemini(r).get("total_tokens"), 0)
        for r in runs
    )

    live_runs = [
        r
        for r in runs
        if _gemini(r) and _gemini(r).get("is_stub") is False
    ]

    stub_runs = [
        r
        for r in runs
        if _gemini(r) and _gemini(r).get("is_stub") is True
    ]

    packs = {
        _lynkmesh(r).get("context_pack_id")
        for r in runs
        if _lynkmesh(r).get("context_pack_id")
    }

    return {
        "total_runs": len(runs),
        "succeeded": sum(1 for r in runs if r.get("result_status") == "succeeded"),
        "failed": sum(1 for r in runs if r.get("result_status") == "failed"),
        "reviewed": len(reviewed),
        "approved": len(approved),
        "approval_rate": (len(approved) / len(reviewed)) if reviewed else None,
        "total_gemini_tokens": total_tokens,
        "distinct_context_packs": len(packs),
        "live_runs": len(live_runs),
        "stub_runs": len(stub_runs),
    }


@router.get("/api/runs")
def api_runs(request: Request, limit: int = 100):
    """Return recent ExecutionLog records."""
    return request.app.state.store.list_runs(limit=limit)


@router.get("/api/runs/{run_id}")
def api_run(request: Request, run_id: str):
    """Return one ExecutionLog record by run_id."""
    run = request.app.state.store.get_run(run_id)
    if not run:
        return {"error": "not found"}
    return run


@router.get("/api/summary")
def api_summary(request: Request):
    """Return dashboard KPI summary."""
    return _summary(request.app.state.store)


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    """Render the judge-facing evidence dashboard."""
    store = request.app.state.store
    runs = store.list_runs(limit=100)

    context = {
        "request": request,
        "runs": runs,
        "latest_run": runs[0] if runs else None,
        "summary": _summary(store),
    }

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context=context,
    )