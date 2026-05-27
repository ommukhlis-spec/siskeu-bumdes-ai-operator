from app.evidence.run_logger import RunLogger
from app.evidence.schema import LynkMeshRef, PromptRef
from app.evidence.store import LocalJsonlStore


def test_local_store_roundtrip(tmp_path):
    store = LocalJsonlStore(str(tmp_path))
    logger = RunLogger(store, str(tmp_path))
    rid = RunLogger.new_run_id()
    log = logger.start_run(
        run_id=rid,
        agent_name="report_explainer",
        agent_version="1.0.0",
        tenant_ref="sha256:abc",
        period="2026-04",
        input_summary="x",
        lynkmesh=LynkMeshRef(context_pack_id="h"),
        prompt=PromptRef(prompt_id="p", prompt_version="v1", prompt_sha256="s"),
    )
    log.result_status = "succeeded"
    logger.finalize(log)

    assert store.get_run(rid)["run_id"] == rid
    assert len(store.list_runs()) == 1
    assert (tmp_path / "runs.jsonl").exists()

    updated = store.update_review(
        rid, {"status": "approved", "reviewer_ref": "rev", "reviewed_at": None, "notes": "ok"}
    )
    assert updated["human_review"]["status"] == "approved"
