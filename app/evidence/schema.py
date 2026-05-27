"""Pydantic models for the agent execution log and evidence items.

The ExecutionLog is the heart of the evidence pipeline. One document per run.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class LynkMeshRef(BaseModel):
    context_pack_id: str                 # content hash of the pack
    graph_id: Optional[str] = None
    build_id: Optional[str] = None
    profile: str = "balanced"
    generator_version: Optional[str] = None
    schema_version: Optional[str] = None
    token_estimate: Optional[int] = None


class PromptRef(BaseModel):
    prompt_id: str
    prompt_version: str
    prompt_sha256: str


class GeminiUsage(BaseModel):
    model: str
    response_id: Optional[str] = None
    finish_reason: Optional[str] = None
    prompt_tokens: int = 0
    candidates_tokens: int = 0
    total_tokens: int = 0
    latency_ms: Optional[int] = None
    temperature: float = 0.2
    is_stub: bool = False


class HumanReview(BaseModel):
    status: str = "pending"              # pending | approved | rejected | edited
    reviewer_ref: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    notes: Optional[str] = None


class ExecutionLog(BaseModel):
    run_id: str
    agent_name: str
    agent_version: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    tenant_ref: str                      # hashed / redacted, never a raw name
    period: str
    input_summary: str
    data_classification: str = "synthetic"   # synthetic | redacted | real
    lynkmesh: LynkMeshRef
    prompt: PromptRef
    gemini: Optional[GeminiUsage] = None
    cost_estimate_usd: Optional[float] = None
    artifacts: dict[str, str] = Field(default_factory=dict)
    human_review: HumanReview = Field(default_factory=HumanReview)
    result_status: str = "running"       # running | succeeded | failed
    error: Optional[str] = None


class EvidenceItem(BaseModel):
    evidence_id: str
    category: str   # product | ai_execution | revenue_historical | revenue_xprize | customer | cost | marketing
    title: str
    date: Optional[str] = None
    file_ref: Optional[str] = None
    redaction_status: str = "redacted"   # redacted | synthetic | raw_private
    customer_ref: Optional[str] = None
    counts_as_xprize_revenue: bool = False
    linked_run_ids: list[str] = Field(default_factory=list)
    notes: Optional[str] = None
