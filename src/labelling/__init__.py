"""Labelling harness package — v3.

Exposes the core data types, the Labeller ABC, and the config loader.
Concrete labellers (RemoteVlmLabeller, HybridLabeller) live in sibling modules.
"""
from src.labelling.base import Detection, LabelOutput, Labeller, LabellerError
from src.labelling.config import ConfigError, LabellerConfig, load_config

__all__ = [
    "ConfigError",
    "Detection",
    "LabelOutput",
    "Labeller",
    "LabellerConfig",
    "LabellerError",
    "load_config",
]
