"""Report data source.

Starts with a synthetic JSON fixture. Real read-only sources are stubbed with
clean interfaces + TODOs:
- HttpReportSource: read-only Siskeu HTTP endpoint.
- DbViewReportSource: read-only DB view.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class ReportSource(Protocol):
    def get_monthly_report(self, tenant_ref: str, period: str) -> dict: ...


class SyntheticReportSource:
    def __init__(self, fixture_dir: str):
        self.fixture_dir = Path(fixture_dir)

    def get_monthly_report(self, tenant_ref: str, period: str) -> dict:
        path = self.fixture_dir / f"synthetic_report_{period}.json"
        if not path.exists():
            raise FileNotFoundError(
                f"No synthetic fixture for period {period} at {path}. "
                f"Run scripts/seed_synthetic_tenant.py {period} to create one."
            )
        return json.loads(path.read_text(encoding="utf-8"))


class HttpReportSource:
    """TODO: read-only HTTP integration with Siskeu.
    Expected: GET {base_url}/api/reports/{tenant}/{period} (read-only, auth'd),
    returning the same JSON shape as the synthetic fixture."""

    def __init__(self, base_url: str, api_token: str | None = None):
        self.base_url = base_url
        self.api_token = api_token

    def get_monthly_report(self, tenant_ref: str, period: str) -> dict:
        raise NotImplementedError("HttpReportSource is not implemented yet (read-only Siskeu endpoint).")


class DbViewReportSource:
    """TODO: read-only DB view integration.
    Expected: SELECT from a read-only reporting VIEW; never write."""

    def __init__(self, dsn: str):
        self.dsn = dsn

    def get_monthly_report(self, tenant_ref: str, period: str) -> dict:
        raise NotImplementedError("DbViewReportSource is not implemented yet (read-only DB view).")


def get_report_source(config) -> ReportSource:
    kind = config.report_source
    if kind == "synthetic":
        return SyntheticReportSource(config.report_fixture_dir)
    if kind == "http":
        raise NotImplementedError("Set REPORT_SOURCE=synthetic for now; HTTP source is a TODO.")
    if kind == "dbview":
        raise NotImplementedError("Set REPORT_SOURCE=synthetic for now; DB view source is a TODO.")
    raise ValueError(f"Unknown REPORT_SOURCE={kind!r}")
