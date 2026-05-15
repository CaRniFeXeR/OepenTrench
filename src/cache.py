"""Build / load a parquet cache of photo metadata for the dataset.

Use from notebooks: `df = load_or_build_photo_index()`.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path
from typing import Optional

import pandas as pd
from tqdm.auto import tqdm

from .photos import extract_photo_record, iter_photo_paths

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FOTOS = ROOT / "project-resources" / "Fotos"
DEFAULT_CACHE = ROOT / "data" / "cache" / "photo_index.parquet"


def build_photo_index(fotos_dir: Path = DEFAULT_FOTOS, workers: int = 8) -> pd.DataFrame:
    paths = list(iter_photo_paths(fotos_dir))
    rows = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for rec in tqdm(ex.map(extract_photo_record, paths), total=len(paths), desc="EXIF scan"):
            d = asdict(rec)
            d["path"] = str(rec.path)
            rows.append(d)
    df = pd.DataFrame(rows)
    # parquet doesn't love datetime mixing — coerce
    for col in ("exif_datetime", "filename_date"):
        df[col] = pd.to_datetime(df[col], errors="coerce")
    df["best_datetime"] = df["exif_datetime"].fillna(df["filename_date"])
    return df


def load_or_build_photo_index(fotos_dir: Path = DEFAULT_FOTOS,
                              cache: Path = DEFAULT_CACHE,
                              force: bool = False) -> pd.DataFrame:
    if cache.exists() and not force:
        return pd.read_parquet(cache)
    cache.parent.mkdir(parents=True, exist_ok=True)
    df = build_photo_index(fotos_dir)
    df.to_parquet(cache, index=False)
    return df
