"""Report data sources and interactive synthetic report builder.

The production Siskeu BUMDes app can stay outside this AI Operator MVP.
For XPRIZE/demo use we support:
- fixture reports from data/fixtures,
- custom synthetic/redacted reports submitted from the dashboard console,
- future read-only HTTP/DB integrations.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ReportSource(Protocol):
    def get_monthly_report(self, tenant_ref: str, period: str) -> dict: ...


def _num(value: Any, default: float = 0) -> float:
    """Coerce dashboard input into a safe number."""
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(_num(value, default))
    except (TypeError, ValueError):
        return default


def build_custom_synthetic_report(payload: dict) -> dict:
    """Build the same report shape as the fixture from dashboard/API input.

    This deliberately marks the report as synthetic/redacted so the public demo
    does not imply raw production BUMDes data is being processed.
    """
    period = str(payload.get("period") or "2026-04")
    tenant_ref = str(payload.get("tenant_ref") or "synthetic-tenant-001")
    currency = str(payload.get("currency") or "IDR")

    cash_beginning = _int(payload.get("cash_beginning"), 12_000_000)
    cash = _int(payload.get("cash_ending"), 17_500_000)
    revenue = _int(payload.get("revenue"), 45_200_000)
    cogs = _int(payload.get("cost_of_goods_sold"), 21_500_000)
    operating_expenses = _int(payload.get("operating_expenses"), 9_800_000)
    receivables = _int(payload.get("receivables"), 7_200_000)
    inventory = _int(payload.get("inventory"), 12_400_000)
    fixed_assets_net = _int(payload.get("fixed_assets_net"), 64_000_000)
    payables = _int(payload.get("payables"), 5_400_000)
    short_term_debt = _int(payload.get("short_term_debt"), 8_000_000)
    village_capital = _int(payload.get("village_capital"), 95_000_000)
    prev_month_net_income = _int(payload.get("prev_month_net_income"), 11_200_000)

    net_income = revenue - cogs - operating_expenses
    total_assets = cash + receivables + inventory + fixed_assets_net
    total_liabilities = payables + short_term_debt
    retained_earnings = max(0, total_assets - total_liabilities - village_capital)
    total_equity = village_capital + retained_earnings

    # Keep the trial balance balanced for this demo payload by construction.
    total_debit = total_assets + cogs + operating_expenses
    total_credit = total_liabilities + total_equity + revenue
    trial_total = max(total_debit, total_credit)

    notes = str(payload.get("notes") or "Synthetic dashboard input for AI Operator demo.")

    return {
        "period": period,
        "tenant_ref_input": tenant_ref,
        "tenant": {
            "tenant_name": "BUMDes Demo Interactive (SYNTHETIC)",
            "village": "Desa Demo",
            "operator_name": "Operator Demo",
            "contact_email": "redacted@example.test",
        },
        "currency": currency,
        "data_classification": "synthetic",
        "input_notes": notes,
        "income_statement": {
            "revenue": revenue,
            "cost_of_goods_sold": cogs,
            "operating_expenses": operating_expenses,
            "net_income": net_income,
            "prev_month_net_income": prev_month_net_income,
        },
        "balance_sheet": {
            "assets": {
                "cash_beginning": cash_beginning,
                "cash": cash,
                "receivables": receivables,
                "inventory": inventory,
                "fixed_assets_net": fixed_assets_net,
                "total_assets": total_assets,
            },
            "liabilities": {
                "payables": payables,
                "short_term_debt": short_term_debt,
                "total_liabilities": total_liabilities,
            },
            "equity": {
                "village_capital": village_capital,
                "retained_earnings": retained_earnings,
                "total_equity": total_equity,
            },
        },
        "trial_balance": {
            "total_debit": trial_total,
            "total_credit": trial_total,
            "balanced": True,
        },
        "units": [
            {"name": "Unit Air Bersih", "net_income": _int(payload.get("unit_air_bersih"), 5_200_000)},
            {"name": "Unit Simpan Pinjam", "net_income": _int(payload.get("unit_simpan_pinjam"), 6_100_000)},
            {"name": "Unit Toko Desa", "net_income": _int(payload.get("unit_toko_desa"), 2_600_000)},
        ],
        "flags": {
            "unposted_drafts": _int(payload.get("unposted_drafts"), 1),
            "missing_opening_balance_accounts": _int(payload.get("missing_opening_balance_accounts"), 0),
            "cash_delta": cash - cash_beginning,
        },
    }


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
    """Future read-only HTTP integration with Siskeu.

    Expected: GET {base_url}/api/reports/{tenant}/{period} (read-only, auth'd),
    returning the same JSON shape as the synthetic fixture.
    """

    def __init__(self, base_url: str, api_token: str | None = None):
        self.base_url = base_url
        self.api_token = api_token

    def get_monthly_report(self, tenant_ref: str, period: str) -> dict:
        raise NotImplementedError("HttpReportSource is not implemented yet (read-only Siskeu endpoint).")


class DbViewReportSource:
    """Future read-only DB view integration. Never write to production tables."""

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
