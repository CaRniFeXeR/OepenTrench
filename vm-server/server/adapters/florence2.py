"""Stub — microsoft/Florence-2-large. Not implemented this session."""
from __future__ import annotations

from typing import List

from server.adapters.base import Adapter
from server.schema import DetectRequest, DetectResponse


class Florence2Adapter(Adapter):
    @property
    def model_id(self) -> str:
        return "florence-2-large"

    @property
    def classes(self) -> List[str]:
        return ["duct", "ruler", "whitepaper"]

    def load_model(self) -> None:
        raise NotImplementedError(
            "Florence2Adapter is a stub. Spec defers to next session."
        )

    def detect(self, req: DetectRequest) -> DetectResponse:
        raise NotImplementedError("Florence2Adapter is a stub.")
