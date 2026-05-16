"""Adapter ABC — one class per model family."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from server.schema import DetectRequest, DetectResponse


class Adapter(ABC):
    """Abstract base for every model adapter.

    Lifecycle:
        adapter = AdapterSubclass()
        adapter.load_model()        # once at server startup
        adapter.detect(req)         # per request
    """

    @abstractmethod
    def load_model(self) -> None: ...

    @abstractmethod
    def detect(self, req: DetectRequest) -> DetectResponse: ...

    @property
    @abstractmethod
    def model_id(self) -> str: ...

    @property
    @abstractmethod
    def classes(self) -> List[str]: ...
