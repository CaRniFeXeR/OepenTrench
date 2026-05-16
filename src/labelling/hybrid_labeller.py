"""Hybrid labeller — REMOTE-VLM + operator-mediated Claude arbitration.

Not implemented this session. The skeleton exists so the ABC contract is
testable and so a future session can add the concrete implementation without
restructuring imports.

Hybrid-mode mechanics, when implemented, will be operator-mediated per spec
§3 and §14 ("Hybrid mode shape → per-image arbitration ... operator-mediated
via Agent dispatch"): the Python harness runs ``remote-vlm`` first and writes
its output; Claude (in the Claude Code session) reads that output, dispatches
Agent calls that arbitrate per image, and writes
``labelling/runs/hybrid-<profile>_<ts>/`` with the same on-disk shape.

Spec: docs/superpowers/specs/2026-05-15-labelling-harness-v3-design.md §4.1, §5.5.
"""
from __future__ import annotations

from pathlib import Path

from src.labelling.base import LabelOutput, Labeller
from src.labelling.config import LabellerConfig


class HybridLabeller(Labeller):
    """Placeholder. ``mode: hybrid`` is not selectable in this session's config schema."""

    def __init__(self, config: LabellerConfig) -> None:
        self.config = config

    @property
    def name(self) -> str:
        return f"hybrid:{self.config.model}"

    def label(self, image_path: Path) -> LabelOutput:
        raise NotImplementedError(
            "HybridLabeller is not implemented this session. See "
            "docs/superpowers/specs/2026-05-15-labelling-harness-v3-design.md "
            "§14 for the next-session sketch."
        )
