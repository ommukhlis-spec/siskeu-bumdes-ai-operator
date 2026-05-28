from app.agents.report_explainer import ReportExplainerAgent
from app.config import load_config
from app.evidence.run_logger import RunLogger
from app.evidence.store import LocalJsonlStore
from app.gemini.client import GeminiClient
from app.lynkmesh.context_loader import ContextLoader
from app.siskeu.report_adapter import SyntheticReportSource


def test_report_explainer_end_to_end_stub(tmp_path, monkeypatch):
    monkeypatch.delenv("GEMINI_MODE", raising=False)
    monkeypatch.delenv("GOOGLE_GENAI_USE_VERTEXAI", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_LOCATION", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-flash")

    cfg = load_config()
    store = LocalJsonlStore(str(tmp_path))
    logger = RunLogger(store, str(tmp_path))
    loader = ContextLoader(cfg.lynkmesh_pack_path)
    gemini = GeminiClient(api_key="", model=cfg.gemini_model)
    source = SyntheticReportSource(cfg.report_fixture_dir)

    agent = ReportExplainerAgent(
        config=cfg,
        logger=logger,
        context_loader=loader,
        gemini=gemini,
        report_source=source,
    )

    log, briefing = agent.run("synthetic-tenant-001", "2026-04")

    assert log.result_status == "succeeded"
    assert log.gemini is not None and log.gemini.total_tokens > 0
    assert log.gemini.is_stub is True
    assert briefing
