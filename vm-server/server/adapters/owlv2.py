"""Stub — google/owlv2-large-patch14-ensemble. Not implemented this session."""
from __future__ import annotations

from typing import List

from server.adapters.base import Adapter
from server.schema import DetectRequest, DetectResponse


class OWLv2Adapter(Adapter):
    @property
    def model_id(self) -> str:
        return "owlv2-large-patch14-ensemble"

    @property
    def classes(self) -> List[str]:
        return ["duct", "ruler", "whitepaper", "sitetag"]

    def load_model(self) -> None:
        raise NotImplementedError(
            "OWLv2Adapter is a stub. Spec defers to next session."
        )

    def detect(self, req: DetectRequest) -> DetectResponse:
        raise NotImplementedError("OWLv2Adapter is a stub.")
