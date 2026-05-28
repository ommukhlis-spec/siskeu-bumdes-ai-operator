"""Read-only dashboard + JSON APIs over the run store."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))


def _summary(store) -> dict:
    runs = store.list_runs(limit=1000)
    reviewed = [r for r in runs if (r.get("human_review") or {}).get("status") in ("approved", "rejected", "edited")]
    approved = [r for r in reviewed if (r.get("human_review") or {}).get("status") == "approved"]
    total_tokens = sum((r.get("gemini") or {}).get("total_tokens", 0) for r in runs)
    live_runs = [r for r in runs if not (r.get("gemini") or {}).get("is_stub", True)]
    stub_runs = [r for r in runs if (r.get("gemini") or {}).get("is_stub", False)]
    packs = {(r.get("lynkmesh") or {}).get("context_pack_id") for r in runs if r.get("lynkmesh")}
    return {
        "total_runs": len(runs),
        "succeeded": sum(1 for r in runs if r.get("result_status") == "succeeded"),
        "failed": sum(1 for r in runs if r.get("result_status") == "failed"),
        "reviewed": len(reviewed),
        "approved": len(approved),
        "approval_rate": (len(approved) / len(reviewed)) if reviewed else None,
        "total_gemini_tokens": total_tokens,
        "distinct_context_packs": len([p for p in packs if p]),
        "live_runs": len(live_runs),
        "stub_runs": len(stub_runs),
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
        "dashboard.html",
        {
            "request": request,
            "runs": runs,
            "latest_run": runs[0] if runs else None,
            "summary": _summary(store),
        },
    )
