"""Minimal agent contract."""
from __future__ import annotations


class Agent:
    name: str = "agent"
    version: str = "0.0.0"

    def run(self, *args, **kwargs):
        raise NotImplementedError
