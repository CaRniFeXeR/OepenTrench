from __future__ import annotations

import re
import threading
from pathlib import Path

import easyocr
from sqlmodel import Session

from src.api.models import AssetKind, GpsCoordinates, Project, ProjectAsset
from src.api.uploads import get_upload_root, project_asset_abs_path

_INCOMPLETE_MSG = "Geoinformation is not complete (could not read latitude/longitude with N/S and E/W from the image)."

_reader: easyocr.Reader | None = None
_reader_lock = threading.Lock()


def _get_reader() -> easyocr.Reader:
    global _reader
    with _reader_lock:
        if _reader is None:
            _reader = easyocr.Reader(["de"], verbose=False)
        return _reader


def _float_de(s: str) -> float:
    """Parse a number that may use ',' as decimal separator (common in DE OCR)."""
    return float(s.replace(",", ".").replace(" ", ""))


def _dms_to_signed_decimal(deg: float, minutes: float, seconds: float, hemisphere: str) -> float:
    v = deg + minutes / 60.0 + seconds / 3600.0
    h = hemisphere.upper()
    if h in ("S", "W"):
        v = -v
    return v


# Degrees: * or °, minutes: ', seconds may use comma decimals; hemisphere suffix.
_LAT_DMS = re.compile(
    r"(\d{1,3})\s*[*°]\s*(\d{1,2})\s*['′]\s*([\d,\.]+)\s*[\"″]?\s*([NS])\b",
    re.IGNORECASE,
)
_LON_DMS = re.compile(
    r"(\d{1,3})\s*[*°]\s*(\d{1,2})\s*['′]\s*([\d,\.]+)\s*[\"″]?\s*([EWO])\b",
    re.IGNORECASE,
)

# Decimal degrees with explicit hemisphere; ',' allowed as decimal separator (DE).
_NUM = r"\d{1,3}(?:[.,]\d+)?"
_LAT_DEC = re.compile(
    rf"(?:\b([NS])\s*({_NUM})\b)|(?:\b({_NUM})\s*°?\s*([NS])\b)",
    re.IGNORECASE,
)
_LON_DEC = re.compile(
    rf"(?:\b([EWO])\s*({_NUM})\b)|(?:\b({_NUM})\s*°?\s*([EWO])\b)",
    re.IGNORECASE,
)


def _parse_lat_lon_from_ocr_text(text: str) -> tuple[float, float] | None:
    text = re.sub(r"\s+", " ", text).strip()

    lat_m = _LAT_DMS.search(text)
    lon_m = _LON_DMS.search(text)
    if lat_m and lon_m:
        try:
            d1, m1, s1, h1 = lat_m.group(1), lat_m.group(2), lat_m.group(3), lat_m.group(4)
            d2, m2, s2, h2 = lon_m.group(1), lon_m.group(2), lon_m.group(3), lon_m.group(4)
            lat = _dms_to_signed_decimal(float(d1), float(m1), _float_de(s1), h1)
            lon = _dms_to_signed_decimal(float(d2), float(m2), _float_de(s2), h2)
            if h1.upper() not in "NS" or h2.upper() not in "EWO":
                return None
            return lat, lon
        except (ValueError, ArithmeticError):
            pass

    lat_m2 = _LAT_DEC.search(text)
    lon_m2 = _LON_DEC.search(text)
    if not lat_m2 or not lon_m2:
        return None

    def _dec_from_lat_match(m: re.Match[str]) -> tuple[float, str] | None:
        if m.group(1) is not None and m.group(2) is not None:
            return _float_de(m.group(2)), m.group(1)
        if m.group(3) is not None and m.group(4) is not None:
            return _float_de(m.group(3)), m.group(4)
        return None

    def _dec_from_lon_match(m: re.Match[str]) -> tuple[float, str] | None:
        if m.group(1) is not None and m.group(2) is not None:
            return _float_de(m.group(2)), m.group(1)
        if m.group(3) is not None and m.group(4) is not None:
            return _float_de(m.group(3)), m.group(4)
        return None

    try:
        lat_pair = _dec_from_lat_match(lat_m2)
        lon_pair = _dec_from_lon_match(lon_m2)
        if lat_pair is None or lon_pair is None:
            return None
        lat_v, lat_h = lat_pair
        lon_v, lon_h = lon_pair
        lat = lat_v if lat_h.upper() == "N" else -lat_v
        lon_hu = lon_h.upper()
        if lon_hu == "W":
            lon = -lon_v
        else:
            lon = lon_v  # E or O (Ost)
        return lat, lon
    except (ValueError, ArithmeticError):
        return None


def _join_ocr_lines(lines: list[str]) -> str:
    return re.sub(r"\s+", " ", " ".join(lines)).strip()


def _read_ocr_lines(path: Path) -> list[str] | None:
    try:
        return _get_reader().readtext(str(path), detail=0)
    except Exception:
        return None


def gps_coordinates_from_image_path(
    image_path: str | Path,
    *,
    print_incomplete: bool = True,
) -> GpsCoordinates | None:
    """Run EasyOCR on a local image and parse GPS as GeoJSON Point (lon, lat)."""
    path = Path(image_path)
    if not path.is_file():
        if print_incomplete:
            print(_INCOMPLETE_MSG)
        return None

    lines = _read_ocr_lines(path)
    if lines is None:
        if print_incomplete:
            print(_INCOMPLETE_MSG)
        return None

    text = _join_ocr_lines(lines)
    parsed = _parse_lat_lon_from_ocr_text(text)
    if parsed is None:
        if print_incomplete:
            print(_INCOMPLETE_MSG)
        return None

    lat, lon = parsed
    if abs(lat) > 90 or abs(lon) > 180:
        if print_incomplete:
            print(_INCOMPLETE_MSG)
        return None
    return GpsCoordinates(coordinates=(lon, lat))


def extract_img_metadata(
    session: Session,
    *,
    project_id: str,
    asset_id: str,
) -> GpsCoordinates | None:
    """OCR image stamp and return parsed GPS as a GeoJSON Point model, or None if missing/unreadable."""
    project = session.get(Project, project_id)
    if project is None:
        raise LookupError("project not found")
    asset = session.get(ProjectAsset, asset_id)
    if asset is None:
        raise LookupError("asset not found")
    if asset.project_id != project_id:
        raise ValueError("asset does not belong to project")
    if asset.kind != AssetKind.image:
        raise ValueError("asset is not an image")

    upload_root = get_upload_root()
    path = project_asset_abs_path(upload_root=upload_root, stored_relpath=asset.stored_relpath)
    if not path.is_file():
        print(_INCOMPLETE_MSG)
        return None

    return gps_coordinates_from_image_path(path, print_incomplete=True)

if __name__ == "__main__":
    print(gps_coordinates_from_image_path('project-resources/Fotos/1_WhatsApp Image 2024-11-04 at 19_29_40.jpeg'))