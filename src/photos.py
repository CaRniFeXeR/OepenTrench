"""Photo metadata extraction utilities (EXIF, GPS, file stats).

Tuned for the ÖpenTrench dataset: ~3,900 mixed-source images
(IMG-* WhatsApp downloads, raw WhatsApp Image *, TimePhoto, etc.).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from PIL import Image, ExifTags, UnidentifiedImageError

_GPS_TAG_ID = next(k for k, v in ExifTags.TAGS.items() if v == "GPSInfo")
_GPS_TAGS = {v: k for k, v in ExifTags.GPSTAGS.items()}

# Filename pattern hints
_DATE_IMG = re.compile(r"IMG-(\d{4})(\d{2})(\d{2})-WA\d+")
_DATE_WHATSAPP = re.compile(r"WhatsApp Image (\d{4})-(\d{2})-(\d{2})")
_DATE_TIMEPHOTO = re.compile(r"TimePhoto_(\d{4})(\d{2})(\d{2})_(\d{6})")
_PREFIX = re.compile(r"^(\d+)_")


@dataclass
class PhotoRecord:
    path: Path
    filename: str
    prefix: Optional[str] = None
    source_kind: str = "unknown"
    filesize: int = 0
    width: Optional[int] = None
    height: Optional[int] = None
    exif_datetime: Optional[datetime] = None
    filename_date: Optional[datetime] = None
    has_exif: bool = False
    has_gps: bool = False
    gps_lat: Optional[float] = None
    gps_lon: Optional[float] = None
    gps_alt: Optional[float] = None
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    error: Optional[str] = None


def _dms_to_deg(dms, ref) -> Optional[float]:
    try:
        d, m, s = [float(x) for x in dms]
        deg = d + m / 60.0 + s / 3600.0
        if ref in ("S", "W"):
            deg = -deg
        return deg
    except Exception:
        return None


def _parse_exif_dt(raw) -> Optional[datetime]:
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y:%m:%d %H:%M:%S")
    except Exception:
        return None


def classify_source(name: str) -> str:
    base = re.sub(r"^\d+_", "", name)
    if base.startswith("IMG-") and "WA" in base:
        return "whatsapp_img"
    if base.startswith("WhatsApp Image"):
        return "whatsapp_raw"
    if base.startswith("TimePhoto"):
        return "timephoto"
    return "other"


def parse_filename_date(name: str) -> Optional[datetime]:
    for pat in (_DATE_IMG, _DATE_WHATSAPP):
        m = pat.search(name)
        if m:
            try:
                return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except Exception:
                return None
    m = _DATE_TIMEPHOTO.search(name)
    if m:
        try:
            t = m.group(4)
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)),
                            int(t[:2]), int(t[2:4]), int(t[4:6]))
        except Exception:
            return None
    return None


def parse_prefix(name: str) -> Optional[str]:
    m = _PREFIX.match(name)
    return m.group(1) if m else None


def extract_photo_record(path: Path) -> PhotoRecord:
    rec = PhotoRecord(path=path, filename=path.name)
    rec.prefix = parse_prefix(path.name)
    rec.source_kind = classify_source(path.name)
    rec.filename_date = parse_filename_date(path.name)
    try:
        rec.filesize = path.stat().st_size
    except OSError as e:
        rec.error = f"stat:{e}"
        return rec
    try:
        with Image.open(path) as im:
            rec.width, rec.height = im.size
            exif = im._getexif() or {}
    except (UnidentifiedImageError, OSError, ValueError) as e:
        rec.error = f"open:{type(e).__name__}"
        return rec
    except Exception as e:  # be permissive — EDA tolerates bad files
        rec.error = f"open:{type(e).__name__}"
        return rec

    if not exif:
        return rec
    rec.has_exif = True
    tags = {ExifTags.TAGS.get(k, k): v for k, v in exif.items() if k != _GPS_TAG_ID}
    rec.exif_datetime = _parse_exif_dt(tags.get("DateTimeOriginal") or tags.get("DateTime"))
    rec.camera_make = (tags.get("Make") or "").strip() or None
    rec.camera_model = (tags.get("Model") or "").strip() or None

    gps_raw = exif.get(_GPS_TAG_ID)
    if gps_raw:
        gps = {ExifTags.GPSTAGS.get(k, k): v for k, v in gps_raw.items()}
        lat = _dms_to_deg(gps.get("GPSLatitude"), gps.get("GPSLatitudeRef"))
        lon = _dms_to_deg(gps.get("GPSLongitude"), gps.get("GPSLongitudeRef"))
        if lat is not None and lon is not None:
            rec.has_gps = True
            rec.gps_lat = lat
            rec.gps_lon = lon
        alt = gps.get("GPSAltitude")
        if alt is not None:
            try:
                rec.gps_alt = float(alt)
            except Exception:
                pass
    return rec


def iter_photo_paths(root: Path) -> Iterable[Path]:
    exts = {".jpg", ".jpeg", ".png", ".heic", ".webp"}
    for p in sorted(root.iterdir()):
        if p.is_file() and p.suffix.lower() in exts:
            yield p


def best_effort_datetime(rec: PhotoRecord) -> Optional[datetime]:
    return rec.exif_datetime or rec.filename_date
