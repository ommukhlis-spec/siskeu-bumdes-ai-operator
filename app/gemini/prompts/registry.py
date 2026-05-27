"""Loads versioned prompt files and computes their SHA-256, so every run can
prove exactly which instructions produced its output."""
from __future__ import annotations

import hashlib
from pathlib import Path

from app.evidence.schema import PromptRef

PROMPTS_DIR = Path(__file__).resolve().parent


def get_prompt(prompt_id: str, version: str) -> tuple[str, PromptRef]:
    path = PROMPTS_DIR / f"{prompt_id}.{version}.md"
    text = path.read_text(encoding="utf-8")
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return text, PromptRef(prompt_id=prompt_id, prompt_version=version, prompt_sha256=f"sha256:{sha}")
