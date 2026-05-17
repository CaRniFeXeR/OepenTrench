from __future__ import annotations

import json
import re
import threading
from pathlib import Path

import easyocr

from src.api.models import GpsCoordinates

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


# DMS: OCR often drops the minute prime or uses * for degrees; seconds may use * too.
# Kept in sync with analyze/ocr_2.py (parse_lat_lon_from_ocr_text).
_LAT_DMS = re.compile(
    r"(\d{1,2})\s*[*°]\s*(\d{1,2})\s*['′*°]?\s*([\d,\.]+)\s*[\"″*]?\s*([NS])\b",
    re.IGNORECASE,
)
_LON_DMS = re.compile(
    r"(\d{1,3})\s*[*°]\s*(\d{1,2})\s*['′*°]?\s*([\d,\.]+)\s*[\"″*]?\s*([EWO])\b",
    re.IGNORECASE,
)

# Decimal degrees with explicit hemisphere; ',' allowed as decimal separator (DE).
_NUM_INNER = r"\d{1,3}(?:[.,]\d+)?"
_LAT_DEC = re.compile(
    rf"(?:\b([NS])\s*({_NUM_INNER})\b)|(?:\b({_NUM_INNER})\s*°?\s*([NS])\b)",
    re.IGNORECASE,
)
_LON_DEC = re.compile(
    rf"(?:\b([EWO])\s*({_NUM_INNER})\b)|(?:\b({_NUM_INNER})\s*°?\s*([EWO])\b)",
    re.IGNORECASE,
)

# Fused / space-separated decimals common in WhatsApp-style stamp OCR.
_FUSED_LAT_LON_RE = re.compile(
    r"\b(4[5-9]|50)\.(\d+?)((?:[89]|1[0-9])\.\d{2,})(?:\s*[+/+-].*)?\s*([EWO])\b",
    re.IGNORECASE,
)
_SPACE_LAT_LON_RE = re.compile(
    r"\b(4[5-9]|50)\s+(\d{6,})\s*([NS])\s+((?:[89]|1[0-9])\.\d{2,})\s*([EWO])\b",
    re.IGNORECASE,
)

# Explicit "Lat … Long …" (or German Breite/Länge) as on some camera / survey overlays.
_LAT_WORD = r"(?:latitude|lat|breite)"
_LON_WORD = r"(?:longitude|long|lon|lng|länge|laenge|lange)"
_NUM_LABELED = r"([-+]?\d{1,3}(?:[.,]\d+)?)"
_LABELED_LAT_THEN_LON = re.compile(
    rf"\b{_LAT_WORD}\b\s*[:\-=]?\s*(?:([NS])\s*)?{_NUM_LABELED}(?:\s*([NS]))?"
    rf".{{0,280}}?"
    rf"\b{_LON_WORD}\b\s*[:\-=]?\s*(?:([EWO])\s*)?{_NUM_LABELED}(?:\s*([EWO]))?",
    re.IGNORECASE,
)
_LABELED_LON_THEN_LAT = re.compile(
    rf"\b{_LON_WORD}\b\s*[:\-=]?\s*(?:([EWO])\s*)?{_NUM_LABELED}(?:\s*([EWO]))?"
    rf".{{0,280}}?"
    rf"\b{_LAT_WORD}\b\s*[:\-=]?\s*(?:([NS])\s*)?{_NUM_LABELED}(?:\s*([NS]))?",
    re.IGNORECASE,
)


def _coords_sane(lat: float, lon: float) -> bool:
    return abs(lat) <= 90 and abs(lon) <= 180


def _apply_lat_hemisphere(lat: float, h: str | None) -> float:
    if not h:
        return lat
    hu = h.upper()
    if hu == "S":
        return -abs(lat)
    if hu == "N":
        return abs(lat) if lat != 0 else lat
    return lat


def _apply_lon_hemisphere(lon: float, h: str | None) -> float:
    if not h:
        return lon
    hu = h.upper()
    if hu == "W":
        return -abs(lon)
    if hu in ("E", "O"):
        return abs(lon) if lon != 0 else lon
    return lon


def _try_labeled_lat_lon_from_text(text: str) -> tuple[float, float] | None:
    """Parse ``Lat … Long …`` / ``Breite … Länge …`` style stamps (decimal degrees)."""
    m = _LABELED_LAT_THEN_LON.search(text)
    if m:
        try:
            h_lat = m.group(3) or m.group(1)
            lat_s = m.group(2)
            h_lon = m.group(6) or m.group(4)
            lon_s = m.group(5)
            lat = _apply_lat_hemisphere(_float_de(lat_s), h_lat)
            lon = _apply_lon_hemisphere(_float_de(lon_s), h_lon)
            if _coords_sane(lat, lon):
                return lat, lon
        except (ValueError, ArithmeticError):
            pass
    m = _LABELED_LON_THEN_LAT.search(text)
    if m:
        try:
            h_lon = m.group(3) or m.group(1)
            lon_s = m.group(2)
            h_lat = m.group(6) or m.group(4)
            lat_s = m.group(5)
            lat = _apply_lat_hemisphere(_float_de(lat_s), h_lat)
            lon = _apply_lon_hemisphere(_float_de(lon_s), h_lon)
            if _coords_sane(lat, lon):
                return lat, lon
        except (ValueError, ArithmeticError):
            pass
    return None


def _try_fused_lat_lon_from_text(text: str) -> tuple[float, float] | None:
    """Recover fused-decimal OCR where the decimal point between lat/lon vanished."""
    m = _FUSED_LAT_LON_RE.search(text)
    if not m:
        return None
    try:
        lat = float(f"{m.group(1)}.{m.group(2)}")
        lon = float(m.group(3))
        h = m.group(4).upper()
        if h == "W":
            lon = -lon
        if not _coords_sane(lat, lon):
            return None
        return lat, lon
    except (ValueError, ArithmeticError):
        return None


def _try_space_lat_lon_from_text(text: str) -> tuple[float, float] | None:
    """Recover space-instead-of-decimal-point style OCR after the degree integer."""
    m = _SPACE_LAT_LON_RE.search(text)
    if not m:
        return None
    try:
        lat_i, lat_frac_digits, lat_h, lon_s, lon_h = (
            m.group(1),
            m.group(2),
            m.group(3).upper(),
            m.group(4),
            m.group(5).upper(),
        )
        lat = float(f"{lat_i}.{lat_frac_digits}")
        lon = _float_de(lon_s.replace(" ", ""))
        if lat_h == "S":
            lat = -lat
        elif lat_h != "N":
            return None
        if lon_h == "W":
            lon = -lon
        elif lon_h not in ("E", "O"):
            return None
        if not _coords_sane(lat, lon):
            return None
        return lat, lon
    except (ValueError, ArithmeticError):
        return None


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
                pass
            elif _coords_sane(lat, lon):
                return lat, lon
        except (ValueError, ArithmeticError):
            pass

    lat_m2 = _LAT_DEC.search(text)
    lon_m2 = _LON_DEC.search(text)
    if lat_m2 and lon_m2:

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
            if lat_pair is not None and lon_pair is not None:
                lat_v, lat_h = lat_pair
                lon_v, lon_h = lon_pair
                lat = lat_v if lat_h.upper() == "N" else -lat_v
                lon_hu = lon_h.upper()
                if lon_hu == "W":
                    lon = -lon_v
                else:
                    lon = lon_v  # E or O (Ost)
                if _coords_sane(lat, lon):
                    return lat, lon
        except (ValueError, ArithmeticError):
            pass

    labeled = _try_labeled_lat_lon_from_text(text)
    if labeled is not None:
        return labeled

    fused = _try_fused_lat_lon_from_text(text)
    if fused is not None:
        return fused
    spaced = _try_space_lat_lon_from_text(text)
    if spaced is not None:
        return spaced
    return None


def _join_ocr_lines(lines: list[str]) -> str:
    return re.sub(r"\s+", " ", " ".join(lines)).strip()


def _read_ocr_lines(path: Path) -> list[str] | None:
    try:
        return _get_reader().readtext(str(path), detail=0)
    except Exception:
        return None

def _read_ocr_lines_from_json(path: Path, original_label: str) -> list[str] | None:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    for item in data["images"]:
        item_relative_to_folder = item["relative_to_folder"]
        if original_label in item_relative_to_folder:
            # #region agent log
            """ try:
                import time as _time

                with open(
                    "/root/git/OepenTrench/.cursor/debug-ebdde5.log",
                    "a",
                    encoding="utf-8",
                ) as _dbg:
                    _dbg.write(
                        json.dumps(
                            {
                                "sessionId": "ebdde5",
                                "hypothesisId": "H2",
                                "location": "extract_img_metadata_service.py:_read_ocr_lines_from_json",
                                "message": "ocr_dump_match",
                                "data": {
                                    "original_label": original_label,
                                    "ocr_dump_path": item_path,
                                },
                                "timestamp": int(_time.time() * 1000),
                            },
                            indent=4,
                        )
                        + "\n"
                    )
            except Exception:
                print("Error writing to debug log")
                pass """
            # #endregion
            return item["lines"]
    return None


def extract_img_metadata(
    image_path: str | Path,
    original_label: str | None = None,
    *,
    print_incomplete: bool = True,
) -> GpsCoordinates | None:
    """OCR a local image stamp and return parsed GPS as a GeoJSON Point, or None if missing/unreadable."""
    path = Path(image_path)
    if not path.is_file():
        if print_incomplete:
            print(_INCOMPLETE_MSG)
        return None

    lines = _read_ocr_lines(path)
    if lines is None:
        lines = _read_ocr_lines_from_json('src/api/services/mistral_ocr_dump.json', original_label)
        if lines is None:
            if print_incomplete:
                print(_INCOMPLETE_MSG)
            return None

    text = _join_ocr_lines(lines)
    parsed = _parse_lat_lon_from_ocr_text(text)
    if parsed is None:
        lines = _read_ocr_lines_from_json('src/api/services/mistral_ocr_dump.json', original_label)
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

    return GpsCoordinates(coordinates=(parsed[1], parsed[0]))
