"""Tests for the structured Cloud Logging emitter.

These tests assert that the emitter prints valid JSON to stdout/stderr with
the expected Cloud Logging fields, and that forbidden content (prompt text,
raw report, briefing summaries, full Gemini responses) never appears.
"""
from __future__ import annotations

import json

import pytest

from app.evidence import structured_cloud_logger as scl


def _build_run(**overrides) -> dict:
    run = {
        "run_id": "run-abc-123",
        "agent_name": "report_explainer",
        "agent_version": "1.0.0",
        "created_at": "2026-05-26T10:00:00+00:00",
        "completed_at": "2026-05-26T10:00:05+00:00",
        "tenant_ref": "sha256:deadbeef",
        "period": "2026-04",
        "input_summary": "Explain 2026-04 monthly report",
        "data_classification": "synthetic",
        "lynkmesh": {
            "context_pack_id": "pack-hash-xyz",
            "graph_id": "g1",
            "build_id": "b1",
            "profile": "balanced",
            "generator_version": "1.0.0",
            "schema_version": "lynkmesh.v1",
            "token_estimate": 1234,
        },
        "prompt": {
            "prompt_id": "report_explanation",
            "prompt_version": "v1",
            "prompt_sha256": "sha256:promptsha",
        },
        "gemini": {
            "model": "gemini-2.5-flash",
            "response_id": "resp-1",
            "finish_reason": "STOP",
            "prompt_tokens": 100,
            "candidates_tokens": 200,
            "total_tokens": 300,
            "latency_ms": 1500,
            "temperature": 0.2,
            "is_stub": True,
        },
        "artifacts": {
            "prompt_ref": "data/runs/run-abc-123/prompt.txt",
            "redacted_report_ref": "data/runs/run-abc-123/report_redacted.json",
            "gemini_response_ref": "data/runs/run-abc-123/response.json",
        },
        "human_review": {
            "status": "pending",
            "reviewer_ref": None,
            "reviewed_at": None,
            "notes": None,
        },
        "result_status": "succeeded",
        "error": None,
    }
    run.update(overrides)
    return run


def _parse_emitted(captured) -> list[dict]:
    lines: list[dict] = []
    for blob in (captured.out, captured.err):
        for line in blob.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                lines.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return lines


def test_emit_execution_log_finalized_includes_required_fields(capsys, monkeypatch):
    monkeypatch.setenv("STRUCTURED_CLOUD_LOGGING_ENABLED", "true")
    scl.emit_execution_log_finalized(_build_run())
    events = _parse_emitted(capsys.readouterr())
    assert len(events) == 1
    e = events[0]

    assert e["event_type"] == "execution_log_finalized"
    assert e["service"] == "siskeu-bumdes-ai-operator"
    assert e["evidence_type"] == "execution_log"
    assert e["schema_version"] == "execution_log_cloud_event.v1"
    assert e["severity"] == "INFO"
    assert e["cloud_run_safe"] is True
    assert e["run_id"] == "run-abc-123"
    assert e["agent_name"] == "report_explainer"
    assert e["agent_version"] == "1.0.0"
    assert e["period"] == "2026-04"
    assert e["data_classification"] == "synthetic"
    assert e["result_status"] == "succeeded"
    assert e["approved"] is False

    assert e["lynkmesh"]["context_pack_id"] == "pack-hash-xyz"
    assert e["lynkmesh"]["graph_id"] == "g1"
    assert e["lynkmesh"]["build_id"] == "b1"
    assert e["lynkmesh"]["schema_version"] == "lynkmesh.v1"
    assert e["lynkmesh"]["generator_version"] == "1.0.0"
    assert e["lynkmesh"]["token_estimate"] == 1234

    assert e["prompt"]["prompt_id"] == "report_explanation"
    assert e["prompt"]["prompt_version"] == "v1"
    assert e["prompt"]["prompt_sha256"] == "sha256:promptsha"

    assert e["gemini"]["model"] == "gemini-2.5-flash"
    assert e["gemini"]["total_tokens"] == 300
    assert e["gemini"]["is_stub"] is True

    assert e["human_review"]["status"] == "pending"


def test_emit_does_not_include_forbidden_fields(capsys, monkeypatch):
    monkeypatch.setenv("STRUCTURED_CLOUD_LOGGING_ENABLED", "true")
    run = _build_run()
    run["artifacts"] = {"prompt_ref": "data/runs/x/prompt.txt"}
    run["prompt_text"] = "SECRET-PROMPT-CONTENT"
    run["briefing"] = {"summary": "SECRET-SUMMARY"}
    run["raw_response"] = "SECRET-RESPONSE"

    scl.emit_execution_log_finalized(run)
    raw = capsys.readouterr().out

    assert "SECRET-PROMPT-CONTENT" not in raw
    assert "SECRET-SUMMARY" not in raw
    assert "SECRET-RESPONSE" not in raw
    # Artifact file paths must not leak either.
    assert "data/runs/x/prompt.txt" not in raw
    assert "prompt_text" not in raw
    assert "briefing" not in raw
    assert "raw_response" not in raw
    assert "artifacts" not in raw


def test_emit_failed_run_emits_error_severity_and_truncation(capsys, monkeypatch):
    monkeypatch.setenv("STRUCTURED_CLOUD_LOGGING_ENABLED", "true")
    long_msg = "x" * 800
    run = _build_run(
        result_status="failed",
        error=f"ValueError: {long_msg}",
        gemini=None,
    )
    scl.emit_execution_log_finalized(run)
    events = _parse_emitted(capsys.readouterr())
    assert len(events) == 1
    e = events[0]
    assert e["severity"] == "ERROR"
    assert e["result_status"] == "failed"
    assert e["error_class"] == "ValueError"
    assert len(e["error_message_truncated"]) <= 500


def test_emit_human_review_updated_includes_review_status(capsys, monkeypatch):
    monkeypatch.setenv("STRUCTURED_CLOUD_LOGGING_ENABLED", "true")
    run = _build_run()
    review = {
        "status": "approved",
        "reviewer_ref": "rev-001",
        "reviewed_at": "2026-05-26T11:00:00+00:00",
        "notes": "looks good",
    }
    run["human_review"] = review
    scl.emit_human_review_updated("run-abc-123", review, run)
    events = _parse_emitted(capsys.readouterr())
    assert len(events) == 1
    e = events[0]
    assert e["event_type"] == "human_review_updated"
    assert e["run_id"] == "run-abc-123"
    assert e["human_review"]["status"] == "approved"
    assert e["human_review"]["reviewer_ref"] == "rev-001"
    assert e["approved"] is True


def test_emit_disabled_flag_suppresses_output(capsys, monkeypatch):
    monkeypatch.setenv("STRUCTURED_CLOUD_LOGGING_ENABLED", "false")
    scl.emit_execution_log_finalized(_build_run())
    scl.emit_human_review_updated("run-abc-123", {"status": "approved"})
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_emit_does_not_raise_on_malformed_run(capsys, monkeypatch):
    monkeypatch.setenv("STRUCTURED_CLOUD_LOGGING_ENABLED", "true")
    # Should not raise on minimal / weird payloads.
    scl.emit_execution_log_finalized({})
    scl.emit_execution_log_finalized({"run_id": "r", "lynkmesh": "not-a-dict"})
    scl.emit_human_review_updated("r", None)  # type: ignore[arg-type]
    scl.emit_human_review_updated("r", {"status": "approved"}, run="not-a-dict")  # type: ignore[arg-type]
    events = _parse_emitted(capsys.readouterr())
    # Each call should still produce a JSON line (or at minimum: no crash).
    assert all("event_type" in e for e in events)


def test_unhashed_tenant_ref_is_redacted(capsys, monkeypatch):
    monkeypatch.setenv("STRUCTURED_CLOUD_LOGGING_ENABLED", "true")
    run = _build_run(tenant_ref="Ibu Siti Aminah")
    scl.emit_execution_log_finalized(run)
    events = _parse_emitted(capsys.readouterr())
    assert len(events) == 1
    assert "Ibu Siti Aminah" not in json.dumps(events[0])
    assert events[0]["tenant_ref"] == "redacted"
