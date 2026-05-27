"""Durable run store with a Firestore backend and a local JSONL fallback.

- Firestore is used when GCP_PROJECT is set AND the client imports/initialises.
- Otherwise we transparently fall back to local JSONL (dev mode).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional


class LocalJsonlStore:
    """Writes one JSON file per run plus an append-only runs.jsonl audit log."""

    backend_name = "local_jsonl"

    def __init__(self, runs_dir: str):
        self.dir = Path(runs_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.jsonl = self.dir / "runs.jsonl"

    def _run_path(self, run_id: str) -> Path:
        return self.dir / f"{run_id}.json"

    def save_run(self, run: dict) -> None:
        self._run_path(run["run_id"]).write_text(
            json.dumps(run, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        with self.jsonl.open("a", encoding="utf-8") as f:
            f.write(json.dumps(run, ensure_ascii=False) + "\n")

    def get_run(self, run_id: str) -> Optional[dict]:
        p = self._run_path(run_id)
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

    def list_runs(self, limit: int = 100) -> list[dict]:
        items: list[dict] = []
        for p in self.dir.glob("*.json"):
            try:
                items.append(json.loads(p.read_text(encoding="utf-8")))
            except Exception:
                continue
        items.sort(key=lambda r: r.get("created_at", ""), reverse=True)
        return items[:limit]

    def update_review(self, run_id: str, review: dict) -> Optional[dict]:
        run = self.get_run(run_id)
        if not run:
            return None
        run["human_review"] = review
        self.save_run(run)
        return run


class FirestoreStore:
    backend_name = "firestore"

    def __init__(self, project: str, collection: str):
        from google.cloud import firestore  # lazy import
        self._fs = firestore
        self.db = firestore.Client(project=project)
        self.col = collection

    def save_run(self, run: dict) -> None:
        self.db.collection(self.col).document(run["run_id"]).set(run)

    def get_run(self, run_id: str) -> Optional[dict]:
        doc = self.db.collection(self.col).document(run_id).get()
        return doc.to_dict() if doc.exists else None

    def list_runs(self, limit: int = 100) -> list[dict]:
        q = (
            self.db.collection(self.col)
            .order_by("created_at", direction=self._fs.Query.DESCENDING)
            .limit(limit)
        )
        return [d.to_dict() for d in q.stream()]

    def update_review(self, run_id: str, review: dict) -> Optional[dict]:
        ref = self.db.collection(self.col).document(run_id)
        ref.update({"human_review": review})
        doc = ref.get()
        return doc.to_dict() if doc.exists else None


def get_store(config):
    if config.firestore_enabled:
        try:
            return FirestoreStore(config.gcp_project, config.firestore_collection_runs)
        except Exception as e:  # noqa: BLE001
            print(f"[store] Firestore unavailable ({e}); using local JSONL", file=sys.stderr)
    return LocalJsonlStore(config.runs_dir)
