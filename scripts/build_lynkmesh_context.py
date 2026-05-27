#!/usr/bin/env python3
"""Pluggable LynkMesh context builder.

- StaticPackProvider (default): returns an existing pack fixture; no LynkMesh needed.
- McpPackProvider (TODO): wire to your LynkMesh MCP tools.

Usage:
    LYNKMESH_PROVIDER=static python scripts/build_lynkmesh_context.py
    LYNKMESH_PROVIDER=mcp SISKEU_PROJECT_PATH=/path/to/siskeu_bumdes python scripts/build_lynkmesh_context.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class StaticPackProvider:
    def __init__(self, src: str):
        self.src = Path(src)

    def build_and_fetch(self) -> dict:
        return json.loads(self.src.read_text(encoding="utf-8"))


class McpPackProvider:
    """TODO: implement against your LynkMesh MCP/tooling. Reference sequence:

        1) start_build(project_path=self.project_path)          -> build_id
        2) wait_for_build(build_id)  until job_status == succeeded
        3) get_mesh_context_ai_pack(profile=self.profile)

    Return the pack dict shaped like data/context_packs/sample_context_pack.json
    (must include ai_context_pack.project_identity.content_hash).
    """

    def __init__(self, project_path: str, profile: str = "balanced"):
        self.project_path = project_path
        self.profile = profile

    def build_and_fetch(self) -> dict:
        raise NotImplementedError(
            "Wire McpPackProvider to LynkMesh MCP tools (see docstring)."
        )


def get_provider():
    kind = os.getenv("LYNKMESH_PROVIDER", "static")
    if kind == "static":
        default = REPO_ROOT / "data/context_packs/sample_context_pack.json"
        return StaticPackProvider(os.getenv("LYNKMESH_SAMPLE_PACK", str(default)))
    if kind == "mcp":
        return McpPackProvider(os.getenv("SISKEU_PROJECT_PATH", "/path/to/siskeu_bumdes"))
    raise SystemExit(f"Unknown LYNKMESH_PROVIDER={kind}")


def main():
    provider = get_provider()
    pack = provider.build_and_fetch()
    ident = pack.get("ai_context_pack", {}).get("project_identity", {})
    content_hash = ident.get("content_hash", "unknown")
    out_dir = REPO_ROOT / "data/context_packs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{content_hash}.json"
    out.write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote context pack: {out.name} (content_hash={content_hash})")


if __name__ == "__main__":
    main()
