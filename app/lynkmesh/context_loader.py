"""Loads a LynkMesh context pack (JSON) and exposes:
- the immutable context_pack_id (content hash) used in every run log,
- a compact text block injected into the Gemini prompt.

The raw graph is never sent to the model; only this compact projection is.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.evidence.schema import LynkMeshRef


class ContextLoader:
    def __init__(self, pack_path: str):
        self._pack = json.loads(Path(pack_path).read_text(encoding="utf-8"))
        self._ctx = self._pack.get("ai_context_pack", {})
        self._identity = self._ctx.get("project_identity", {})

    @property
    def context_pack_id(self) -> str:
        return self._identity.get("content_hash", "unknown")

    @property
    def token_estimate(self) -> int:
        return int(self._ctx.get("context_budget", {}).get("estimated_input_tokens", 0) or 0)

    def lynkmesh_ref(self) -> LynkMeshRef:
        return LynkMeshRef(
            context_pack_id=self.context_pack_id,
            graph_id=self._identity.get("graph_id"),
            build_id=self._identity.get("build_id"),
            profile=self._identity.get("profile", "balanced"),
            generator_version=self._identity.get("generator_version"),
            schema_version=self._pack.get("mesh_context_ai_pack_schema_version"),
            token_estimate=self.token_estimate,
        )

    def as_prompt_block(self) -> str:
        exe = self._ctx.get("executive_context", {})
        arch = self._ctx.get("architecture_context", {})
        domain = self._ctx.get("domain_modules", {})
        ntb = exe.get("node_type_breakdown", {})
        lines = [
            "## LynkMesh architectural context (deterministic; grounding only)",
            f"context_pack_id: {self.context_pack_id}",
            f"graph: {exe.get('node_count', '?')} nodes, {exe.get('edge_count', '?')} edges "
            f"(classes={ntb.get('class', '?')}, methods={ntb.get('method', '?')}, files={ntb.get('file', '?')})",
            f"layers: {', '.join(arch.get('layers', []))}",
        ]
        for group, mods in domain.items():
            lines.append(f"{group} modules: {', '.join(mods)}")
        lines.append(
            "Note: 'domain_modules' is a curated enrichment; LynkMesh v0.1 does not "
            "auto-populate domain grouping."
        )
        return "\n".join(lines)
