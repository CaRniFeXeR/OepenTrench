"""Stub — T-Rex2 (image-prompt). Not implemented this session."""
from __future__ import annotations

from typing import List

from server.adapters.base import Adapter
from server.schema import DetectRequest, DetectResponse


class TRex2Adapter(Adapter):
    @property
    def model_id(self) -> str:
        return "t-rex2"

    @property
    def classes(self) -> List[str]:
        return ["duct", "ruler", "whitepaper"]

    def load_model(self) -> None:
        raise NotImplementedError(
            "TRex2Adapter is a stub. Spec defers to next session."
        )

    def detect(self, req: DetectRequest) -> DetectResponse:
        raise NotImplementedError("TRex2Adapter is a stub.")
