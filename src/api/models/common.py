from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel


class AssetKind(str, Enum):
    image = "image"
    geojson = "geojson"


class PhotoDocumentationCategory(str, Enum):
    """Per-photo documentation quality (map node/segment rollup), not workflow status.

    Rules and review workflow: docs/photo-documentation-category.md
    """

    green = "green"
    yellow = "yellow"
    red = "red"


class GpsCoordinates(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: tuple[float, float]  # [longitude, latitude]
