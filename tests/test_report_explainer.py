from app.agents.report_explainer import ReportExplainerAgent
from app.config import load_config
from app.evidence.run_logger import RunLogger
from app.evidence.store import LocalJsonlStore
from app.gemini.client import GeminiClient
from app.lynkmesh.context_loader import ContextLoader
from app.siskeu.report_adapter import SyntheticReportSource


def test_report_explainer_end_to_end_stub(tmp_path):
    cfg = load_config()  # default fixture + pack paths resolve from repo root
    store = LocalJsonlStore(str(tmp_path))
    logger = RunLogger(store, str(tmp_path))
    loader = ContextLoader(cfg.lynkmesh_pack_path)
    gemini = GeminiClient(api_key="", model=cfg.gemini_model)  # force stub
    source = SyntheticReportSource(cfg.report_fixture_dir)
    agent = ReportExplainerAgent(
        config=cfg, logger=logger, context_loader=loader, gemini=gemini, report_source=source
    )

    log, briefing = agent.run("synthetic-tenant-001", "2026-04")

    assert log.result_status == "succeeded"
    assert log.gemini is not None and log.gemini.total_tokens > 0
    assert log.gemini.is_stub is True
    assert log.human_review.status == "pending"
    assert log.lynkmesh.context_pack_id  # grounding recorded
    assert log.tenant_ref.startswith("sha256:")  # PII redacted to a hash
    assert briefing is not None
