"""Redaction: strip tenant PII before anything leaves the boundary or is logged."""
from __future__ import annotations

import copy
import hashlib
import re

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
LONGNUM_RE = re.compile(r"\b\d{6,}\b")


def hash_tenant_ref(value: str) -> str:
    return "sha256:" + hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:16]


def _scrub(s: str) -> str:
    s = EMAIL_RE.sub("[redacted-email]", s)
    s = LONGNUM_RE.sub("[redacted-number]", s)
    return s


def redact_report(report: dict) -> dict:
    """Remove the tenant identity block, replace with a hashed ref, and scrub
    any free-text PII. Numeric financial fields are preserved."""
    r = copy.deepcopy(report)
    tenant = r.pop("tenant", {}) or {}
    name = tenant.get("tenant_name") if isinstance(tenant, dict) else None
    r["tenant_ref"] = hash_tenant_ref(name or r.get("tenant_ref") or "unknown")
    r.setdefault("data_classification", "synthetic")

    def walk(o):
        if isinstance(o, dict):
            return {k: walk(v) for k, v in o.items()}
        if isinstance(o, list):
            return [walk(v) for v in o]
        if isinstance(o, str):
            return _scrub(o)
        return o

    return walk(r)
