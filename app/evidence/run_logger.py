"""Creates, persists, and finalises ExecutionLogs. Logs runs even on failure."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.evidence.schema import ExecutionLog, LynkMeshRef, PromptRef
from app.evidence.structured_cloud_logger import emit_execution_log_finalized


def _now() -> datetime:
    return datetime.now(timezone.utc)


class RunLogger:
    def __init__(self, store, runs_dir: str):
        self.store = store
        self.runs_dir = Path(runs_dir)
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def new_run_id() -> str:
        return str(uuid.uuid4())

    def start_run(
        self,
        *,
        run_id: str,
        agent_name: str,
        agent_version: str,
        tenant_ref: str,
        period: str,
        input_summary: str,
        lynkmesh: LynkMeshRef,
        prompt: PromptRef,
        data_classification: str = "synthetic",
    ) -> ExecutionLog:
        return ExecutionLog(
            run_id=run_id,
            agent_name=agent_name,
            agent_version=agent_version,
            created_at=_now(),
            tenant_ref=tenant_ref,
            period=period,
            input_summary=input_summary,
            data_classification=data_classification,
            lynkmesh=lynkmesh,
            prompt=prompt,
            result_status="running",
        )

    def write_artifact(self, run_id: str, name: str, text: str) -> str:
        d = self.runs_dir / run_id
        d.mkdir(parents=True, exist_ok=True)
        (d / name).write_text(text, encoding="utf-8")
        return f"data/runs/{run_id}/{name}"

    def finalize(self, log: ExecutionLog) -> ExecutionLog:
        log.completed_at = _now()
        run_dict = log.model_dump(mode="json")
        self.store.save_run(run_dict)
        emit_execution_log_finalized(run_dict)
        return log
