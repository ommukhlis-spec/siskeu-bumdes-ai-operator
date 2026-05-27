from datetime import datetime, timezone

from app.evidence.schema import ExecutionLog, LynkMeshRef, PromptRef


def test_execution_log_defaults_and_dump():
    log = ExecutionLog(
        run_id="r1",
        agent_name="report_explainer",
        agent_version="1.0.0",
        created_at=datetime.now(timezone.utc),
        tenant_ref="sha256:abc",
        period="2026-04",
        input_summary="Explain 2026-04 monthly report",
        lynkmesh=LynkMeshRef(context_pack_id="hash123"),
        prompt=PromptRef(prompt_id="report_explanation", prompt_version="v1", prompt_sha256="sha256:x"),
    )
    d = log.model_dump(mode="json")
    assert d["run_id"] == "r1"
    assert d["result_status"] == "running"
    assert d["human_review"]["status"] == "pending"
