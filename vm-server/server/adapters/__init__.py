"""Adapter registry — model name → Adapter subclass."""
from __future__ import annotations

from typing import Dict, Type

from server.adapters.base import Adapter
from server.adapters.florence2 import Florence2Adapter
from server.adapters.grounding_dino import GroundingDinoAdapter
from server.adapters.owlv2 import OWLv2Adapter
from server.adapters.qwen_vl import QwenVLAdapter
from server.adapters.trex2 import TRex2Adapter

ADAPTERS: Dict[str, Type[Adapter]] = {
    "grounding-dino": GroundingDinoAdapter,
    "qwen-vl": QwenVLAdapter,
    "owlv2": OWLv2Adapter,
    "florence2": Florence2Adapter,
    "t-rex2": TRex2Adapter,
}


def get_adapter(name: str) -> Adapter:
    if name not in ADAPTERS:
        raise ValueError(
            f"unknown MODEL={name!r}; known: {sorted(ADAPTERS)}"
        )
    return ADAPTERS[name]()
