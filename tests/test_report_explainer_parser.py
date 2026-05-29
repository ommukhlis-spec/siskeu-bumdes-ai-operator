from app.agents.report_explainer import ReportExplainerAgent


def test_parse_briefing_strips_json_markdown_fence():
    raw = """```json
{"period":"2026-04","summary":"ok","notable_changes":[],"watch_items":[],"caveats":[]}
```"""

    agent = object.__new__(ReportExplainerAgent)
    parsed = agent._parse_briefing(raw)

    assert parsed["period"] == "2026-04"
    assert parsed["summary"] == "ok"
    assert parsed["parse_error"] is False


def test_parse_briefing_accepts_plain_json():
    raw = '{"period":"2026-04","summary":"ok"}'

    agent = object.__new__(ReportExplainerAgent)
    parsed = agent._parse_briefing(raw)

    assert parsed["period"] == "2026-04"
    assert parsed["parse_error"] is False


def test_parse_briefing_returns_parse_error_for_invalid_text():
    raw = "not json"

    agent = object.__new__(ReportExplainerAgent)
    parsed = agent._parse_briefing(raw)

    assert parsed["raw"] == "not json"
    assert parsed["parse_error"] is True
