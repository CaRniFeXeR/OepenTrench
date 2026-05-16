"""Stub — Qwen2.5-VL-7B-Instruct. Not implemented this session."""
from __future__ import annotations

from typing import List

from server.adapters.base import Adapter
from server.schema import DetectRequest, DetectResponse


class QwenVLAdapter(Adapter):
    @property
    def model_id(self) -> str:
        return "qwen2.5-vl-7b-instruct"

    @property
    def classes(self) -> List[str]:
        return ["duct", "ruler", "whitepaper", "sitetag"]

    def load_model(self) -> None:
        raise NotImplementedError(
            "QwenVLAdapter is a stub. Spec defers to next session."
        )

    def detect(self, req: DetectRequest) -> DetectResponse:
        raise NotImplementedError("QwenVLAdapter is a stub.")
