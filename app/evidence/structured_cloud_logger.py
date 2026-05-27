"""Emit sanitized structured JSON logs for ExecutionLog evidence.

These events go to stdout so Cloud Run / Cloud Logging captures them as
structured operational evidence. We do NOT emit prompt text, raw Gemini
responses, briefing summaries, raw report content, customer identity, or
artifact paths. Tenant refs are passed through only if already hashed/redacted
(i.e. prefixed with "sha256:" or the literal "synthetic").

Schema: execution_log_cloud_event.v1
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Optional

SERVICE_NAME = "siskeu-bumdes-ai-operator"
SCHEMA_VERSION = "execution_log_cloud_event.v1"
EVIDENCE_TYPE = "execution_log"
ERROR_MESSAGE_MAX_LEN = 500


def _enabled() -> bool:
    raw = os.getenv("STRUCTURED_CLOUD_LOGGING_ENABLED", "").strip().lower()
    if raw == "":
        return True
    return raw not in {"0", "false", "no", "off"}


def _safe_tenant_ref(tenant_ref: Any) -> Optional[str]:
    if not isinstance(tenant_ref, str) or not tenant_ref:
        return None
    if tenant_ref.startswith("sha256:") or tenant_ref == "synthetic":
        return tenant_ref
    return "redacted"


def _truncate(s: Any, n: int = ERROR_MESSAGE_MAX_LEN) -> Optional[str]:
    if not isinstance(s, str):
        return None
    return s if len(s) <= n else s[:n]


def _lynkmesh_block(run: dict) -> dict:
    lm = run.get("lynkmesh") or {}
    if not isinstance(lm, dict):
        return {}
    out: dict[str, Any] = {}
    for key in (
        "context_pack_id",
        "graph_id",
        "build_id",
        "schema_version",
        "generator_version",
        "token_estimate",
    ):
        v = lm.get(key)
        if v is not None:
            out[key] = v
    return out


def _prompt_block(run: dict) -> dict:
    p = run.get("prompt") or {}
    if not isinstance(p, dict):
        return {}
    out: dict[str, Any] = {}
    for key in ("prompt_id", "prompt_version", "prompt_sha256"):
        v = p.get(key)
        if v is not None:
            out[key] = v
    return out


def _gemini_block(run: dict) -> dict:
    g = run.get("gemini")
    if not isinstance(g, dict):
        return {}
    out: dict[str, Any] = {}
    for key in (
        "model",
        "response_id",
        "finish_reason",
        "prompt_tokens",
        "candidates_tokens",
        "total_tokens",
        "latency_ms",
        "temperature",
        "is_stub",
    ):
        v = g.get(key)
        if v is not None:
            out[key] = v
    return out


def _human_review_block(review: dict | None) -> dict:
    if not isinstance(review, dict):
        return {}
    out: dict[str, Any] = {}
    for key in ("status", "reviewer_ref", "reviewed_at"):
        v = review.get(key)
        if v is not None:
            out[key] = v
    return out


def _approved(review_status: Any) -> bool:
    return isinstance(review_status, str) and review_status.lower() == "approved"


def _emit(payload: dict) -> None:
    if not _enabled():
        return
    try:
        line = json.dumps(payload, ensure_ascii=False, default=str)
        stream = sys.stderr if payload.get("severity") == "ERROR" else sys.stdout
        print(line, file=stream, flush=True)
    except Exception:  # noqa: BLE001
        # Logging must never break the app.
        pass


def _base_payload(run: dict | None, event_type: str) -> dict:
    run = run or {}
    review = run.get("human_review") if isinstance(run.get("human_review"), dict) else None
    result_status = run.get("result_status")
    severity = "ERROR" if result_status == "failed" else "INFO"

    payload: dict[str, Any] = {
        "severity": severity,
        "message": f"{event_type} {run.get('run_id', 'unknown')}",
        "event_type": event_type,
        "service": SERVICE_NAME,
        "evidence_type": EVIDENCE_TYPE,
        "schema_version": SCHEMA_VERSION,
        "cloud_run_safe": True,
        "run_id": run.get("run_id"),
        "agent_name": run.get("agent_name"),
        "agent_version": run.get("agent_version"),
        "period": run.get("period"),
        "data_classification": run.get("data_classification"),
        "result_status": result_status,
        "approved": _approved((review or {}).get("status")),
    }

    tenant = _safe_tenant_ref(run.get("tenant_ref"))
    if tenant is not None:
        payload["tenant_ref"] = tenant

    if result_status == "failed":
        err = run.get("error")
        if isinstance(err, str) and err:
            # ExecutionLog.error is formatted as "ClassName: message"
            if ": " in err:
                cls, _, msg = err.partition(": ")
                payload["error_class"] = cls
                payload["error_message_truncated"] = _truncate(msg)
            else:
                payload["error_class"] = "Error"
                payload["error_message_truncated"] = _truncate(err)

    lm = _lynkmesh_block(run)
    if lm:
        payload["lynkmesh"] = lm
    prompt = _prompt_block(run)
    if prompt:
        payload["prompt"] = prompt
    gemini = _gemini_block(run)
    if gemini:
        payload["gemini"] = gemini
    hr = _human_review_block(review)
    if hr:
        payload["human_review"] = hr

    return payload


def emit_execution_log_finalized(run: dict) -> None:
    """Emit a structured event after a run has been finalized/saved."""
    try:
        payload = _base_payload(run, "execution_log_finalized")
        _emit(payload)
    except Exception:  # noqa: BLE001
        pass


def emit_human_review_updated(
    run_id: str,
    review: dict,
    run: dict | None = None,
) -> None:
    """Emit a structured event after a human review status has been updated."""
    try:
        base_run = dict(run) if isinstance(run, dict) else {}
        base_run["run_id"] = run_id
        base_run["human_review"] = review if isinstance(review, dict) else {}
        payload = _base_payload(base_run, "human_review_updated")
        _emit(payload)
    except Exception:  # noqa: BLE001
        pass
