"""Generate notebooks as .ipynb files from inline definitions.

Run: .venv/bin/python scripts/build_notebooks.py
This keeps notebook source diffable and reproducible without committing JSON by hand.
"""
from __future__ import annotations

from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks"
OUT.mkdir(parents=True, exist_ok=True)


def md(s: str) -> nbf.NotebookNode:
    return nbf.v4.new_markdown_cell(s.strip("\n"))


def code(s: str) -> nbf.NotebookNode:
    return nbf.v4.new_code_cell(s.strip("\n"))


def write(name: str, cells: list[nbf.NotebookNode]) -> Path:
    nb = nbf.v4.new_notebook()
    nb["cells"] = cells
    nb["metadata"] = {
        "kernelspec": {"name": "python3", "display_name": "Python 3"},
        "language_info": {"name": "python"},
    }
    p = OUT / name
    nbf.write(nb, p)
    return p


# ---------- Notebook 1: dataset overview ----------
overview_cells = [
    md("""
# 01 — Dataset overview

**Question this notebook answers:** What is in `project-resources/Fotos/`, and what can we trust about it?

Specifically:
- How many photos, in what formats, from what sources?
- Do we have the metadata the APG brief assumes (GPS, EXIF timestamps)?
- What does the numeric filename prefix (1, 2, 3, …) mean?
- Resolution, file size, time range — what is feasible for inference at scale?

Why it matters: the brief promises "geo-referenced construction site photos." Our sample is mostly WhatsApp downloads, which strips EXIF. That single fact changes the pipeline architecture and is worth confirming before writing any QC logic.
"""),
    code("""
import sys, warnings
from pathlib import Path
sys.path.insert(0, str(Path.cwd().parent))
warnings.filterwarnings("ignore", category=FutureWarning)

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image

from src.cache import load_or_build_photo_index

sns.set_theme(style="whitegrid", context="notebook")
df = load_or_build_photo_index()
df["aspect"] = df["width"] / df["height"]
df["orientation"] = np.where(df["aspect"] >= 1, "landscape", "portrait")
print(f"{len(df):,} photos indexed")
df.head(3)
"""),
    md("## 1 · Headline counts"),
    code("""
n = len(df)
print(f"Total photos:                 {n:,}")
print(f"With ANY EXIF block:          {int(df.has_exif.sum()):,}  ({df.has_exif.mean():.1%})")
print(f"With GPS coordinates:         {int(df.has_gps.sum()):,}  ({df.has_gps.mean():.1%})")
print(f"With camera make/model:       {int(df.camera_make.notna().sum()):,}")
print(f"With EXIF DateTimeOriginal:   {int(df.exif_datetime.notna().sum()):,}")
print(f"Total disk size:              {df.filesize.sum()/1e9:.2f} GB")
print(f"Read errors:                  {int(df.error.notna().sum())}")
"""),
    md("""
**Headline finding — the dataset is mostly stripped of EXIF.** WhatsApp removes camera metadata on upload, so the per-photo GPS and timestamp guarantees the brief implies cannot be assumed on real submissions.

Implication for the pipeline: geo-matching to trench segments cannot rely on per-image GPS. We need a fallback path — lot grouping from filename / folder, plus user-supplied lot↔project mapping at upload time.
"""),
    md("## 2 · Source kind (where did each photo come from?)"),
    code("""
src_counts = df.source_kind.value_counts()
fig, ax = plt.subplots(figsize=(7, 3.5))
src_counts.plot(kind="barh", ax=ax, color="#3b6e8f")
ax.set_xlabel("photos"); ax.set_title("Photos by source kind (inferred from filename)")
for i, v in enumerate(src_counts.values):
    ax.text(v + 30, i, f"{v:,} ({v/len(df):.0%})", va="center")
ax.set_xlim(0, src_counts.max() * 1.15)
plt.tight_layout(); plt.show()
src_counts
"""),
    md("""
- `whatsapp_raw`: filenames like `WhatsApp Image 2024-08-26 at 18_18_36.jpeg` — saved manually from chat. **Date in filename, no EXIF.**
- `whatsapp_img`: filenames like `IMG-20240731-WA0029.jpg` — auto-saved by WhatsApp on Android. Date in filename, no EXIF.
- `timephoto` / `other`: a handful of camera-app captures, some preserve EXIF.

Lesson: filename is the *most reliable* timestamp source we have. EXIF is the exception, not the rule.
"""),
    md("## 3 · Filename prefix — what does the leading number mean?"),
    code("""
prefix = df.prefix.fillna("(none)")
counts = prefix.value_counts().sort_index()
print(counts)
print()
print(f"Photos WITH a prefix:    {int(df.prefix.notna().sum()):,}  ({df.prefix.notna().mean():.1%})")
print(f"Photos WITHOUT a prefix: {int(df.prefix.isna().sum()):,}  ({df.prefix.isna().mean():.1%})")
"""),
    code("""
fig, ax = plt.subplots(figsize=(8, 3.5))
counts.plot(kind="bar", ax=ax, color="#c97f3a")
ax.set_xlabel("filename prefix"); ax.set_ylabel("photos")
ax.set_title("Filename prefix distribution — likely lot or batch identifier")
plt.tight_layout(); plt.show()
"""),
    md("""
**Interpretation:** prefixes are present on ~26% of files, range 1–7, heavily skewed (1 and 2 each have ~470; 3 has ~70; the rest are negligible). Most photos (74%) have no prefix at all.

Working hypothesis: the prefix is a **lot identifier** added during a hand-curation step — only some lots were tagged. Without ground truth we can't confirm. **Need to ask the challenge owner** what the prefix actually represents and whether unprefixed photos belong to a default lot.

This matters because Criterion 5 (duplicates *across lots*) needs a reliable lot label. Filename alone is not enough.
"""),
    md("## 4 · Time coverage (best-effort timestamp per photo)"),
    code("""
ts = df["best_datetime"].dropna()
print(f"Photos with a usable date: {len(ts):,} / {len(df):,}  ({len(ts)/len(df):.1%})")
print(f"Date range: {ts.min().date()} → {ts.max().date()}")
print(f"Span: {(ts.max() - ts.min()).days} days")
"""),
    code("""
fig, ax = plt.subplots(figsize=(11, 3.5))
weekly = ts.dt.to_period("W").dt.to_timestamp().value_counts().sort_index()
ax.bar(weekly.index, weekly.values, width=6, color="#3b6e8f")
ax.set_title("Photos per week (best-effort timestamp)")
ax.set_xlabel("week"); ax.set_ylabel("photos")
plt.tight_layout(); plt.show()
"""),
    md("Construction cadence is visible — quiet weeks vs. spikes likely correspond to specific lot openings."),
    md("## 5 · Resolution and orientation"),
    code("""
fig, axes = plt.subplots(1, 2, figsize=(12, 3.6))
sns.histplot(df.width, bins=40, ax=axes[0], color="#3b6e8f")
axes[0].set_title("Image width (px)"); axes[0].set_xlabel("width")
df.orientation.value_counts().plot(kind="bar", ax=axes[1], color=["#3b6e8f", "#c97f3a"])
axes[1].set_title("Orientation"); axes[1].set_ylabel("photos")
plt.tight_layout(); plt.show()
df[["width", "height", "filesize"]].describe(percentiles=[.1, .5, .9]).round(0)
"""),
    md("""
Median photo is ~1.2 MP and portrait — phone snapshots, not professional documentation rigs. Plenty for vision models but expect noise: motion blur, hands in frame, mixed lighting, occluded ruler.
"""),
    md("## 6 · Spot-check: 24 random photos by source kind"),
    code("""
import random
random.seed(7)
def show_grid(paths, title, ncols=6, scale=2.0):
    nrows = (len(paths) + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(ncols*scale, nrows*scale*1.2))
    axes = np.atleast_2d(axes)
    for ax in axes.ravel(): ax.axis("off")
    for ax, p in zip(axes.ravel(), paths):
        try:
            im = Image.open(p); im.thumbnail((320, 320)); ax.imshow(im)
            ax.set_title(Path(p).name[:30], fontsize=7)
        except Exception as e:
            ax.set_title(f"ERR {e}", fontsize=7)
    fig.suptitle(title, fontsize=11, y=1.02)
    plt.tight_layout(); plt.show()

for src in ["whatsapp_raw", "whatsapp_img", "timephoto"]:
    sub = df[df.source_kind == src]
    if len(sub) == 0: continue
    paths = sub.path.sample(min(12, len(sub)), random_state=7).tolist()
    show_grid(paths, f"{src} — {len(sub):,} photos in dataset")
"""),
    md("""
**What we actually see in the photos** (visual scan):
- Open trenches with visible duct bundles, sand bedding, warning tape (the QC-positive cases)
- Backfilled / finished trenches, asphalt patches
- Reference photos with rulers, tape measures, marked depths
- Wide shots of the road / scene with no trench visible
- Closed manholes, splice cabinets, building facades
- Some photos are blurry, very dark, or have a hand / boot in frame

This visual variance is the actual modelling problem: a single classifier per criterion is unlikely to work; we need **per-criterion detectors** or a **VLM with structured prompts**.
"""),
    md("""
## Takeaways for the pipeline

1. **Don't trust EXIF GPS.** Build the geo-matching path around **upload-time metadata** (project + lot + optional GPS), with EXIF as a bonus confidence boost when present.
2. **Lot grouping is the right unit of evaluation** — not individual photos. Brief explicitly asks for project- and lot-level deficiency reports.
3. **Per-criterion detectors** instead of one classifier — warning tape, sand bedding, depth reference, side view are visually distinct and benefit from specialised checks.
4. **Recall-first thresholds.** The cost of a missed defect (€42M+ network exposure mentioned in the brief) dwarfs the cost of human re-review of a false positive.
5. **Duplicate detection needs perceptual hashing**, not just file hashing — WhatsApp re-encoding changes bytes but preserves the visual content. See `03_examples_and_duplicates.ipynb`.
"""),
]


# ---------- Notebook 2: geo coverage ----------
geo_cells = [
    md("""
# 02 — Geo coverage: trench routes vs. photo locations

**Question this notebook answers:** Where is the project, what does its route topology look like, and can we even map photos to segments?

We have:
- `CLP20417A-P1-B00_Trenches.geojson` — 2,983 LineString segments (the actual underground duct routes)
- `CLP20417A-P1-B00_FCPs.geojson` — 9 Fiber Connection Points (buildings being connected)
- `CLP20417A-P1-B00_FCP_Polygons.geojson` — building footprint polygons
- `CLP20417A-P1-B00_SiteCluster_Polygons.geojson` — the project area polygon
- `Fotos/` — 3,929 photos, **only 5 with GPS EXIF**

Last point is the critical constraint: we mostly cannot geo-match photos to segments directly. This notebook quantifies the route geometry and shows the 5 photos we *can* place.
"""),
    code("""
import sys, warnings
from pathlib import Path
sys.path.insert(0, str(Path.cwd().parent))
warnings.filterwarnings("ignore", category=FutureWarning)

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
import folium
from shapely.geometry import Point

from src.cache import load_or_build_photo_index
from src.geo import load_project, bbox_center

sns.set_theme(style="whitegrid", context="notebook")
ROOT = Path.cwd().parent
proj = load_project(ROOT / "project-resources" / "geojson")
df = load_or_build_photo_index()
print(f"trenches: {len(proj.trenches):,} segments")
print(f"FCPs:     {len(proj.fcps):,}")
print(f"FCP polygons: {len(proj.fcp_polys):,}")
print(f"cluster polygon: {len(proj.cluster):,}")
"""),
    md("## 1 · Trench-segment geometry"),
    code("""
tr_m = proj.trenches.to_crs("EPSG:31287")
tr_m["length_m"] = tr_m.geometry.length
print(f"Total network length:  {tr_m.length_m.sum():,.0f} m  ({tr_m.length_m.sum()/1000:.1f} km)")
print(f"Segment length p50:    {tr_m.length_m.median():.1f} m")
print(f"Segment length p90:    {tr_m.length_m.quantile(0.9):.1f} m")
print(f"Segment length max:    {tr_m.length_m.max():.1f} m")
print(f"Segments < 5 m:        {int((tr_m.length_m < 5).sum()):,}")
"""),
    code("""
fig, ax = plt.subplots(figsize=(10, 3.5))
sns.histplot(tr_m.length_m.clip(upper=80), bins=60, color="#3b6e8f", ax=ax)
ax.set_xlabel("segment length (m, clipped at 80)"); ax.set_title("Trench segment length distribution")
plt.tight_layout(); plt.show()
"""),
    md("""
The network is composed of many short segments. That fits FTTH/FTTB construction: each driveway connection, building feed, and street-crossing gets its own segment. For coverage scoring, "evidence per segment" is unrealistic — we need to roll up to **geo-clusters** (groups of nearby segments) or to **named lots** before scoring.
"""),
    md("## 2 · Execution state per segment"),
    code("""
state = proj.trenches["executionState"].fillna("(none)").value_counts()
print(state)
fig, ax = plt.subplots(figsize=(7, 3))
state.plot(kind="barh", ax=ax, color="#c97f3a")
ax.set_xlabel("segments"); ax.set_title("Trench segments by executionState")
plt.tight_layout(); plt.show()
"""),
    md("""
Segments labeled `Documented` are the ones whose photo evidence we need to verify. Other states (planned, in progress, abandoned) tell us where *no* photo is expected — important to avoid false "missing evidence" flags.
"""),
    md("## 3 · Project footprint + route map"),
    code("""
center_lat, center_lon = bbox_center(proj.trenches)
m = folium.Map(location=[center_lat, center_lon], zoom_start=15,
               tiles="CartoDB positron")

folium.GeoJson(
    proj.cluster.__geo_interface__,
    style_function=lambda f: {"color": "#888", "weight": 1, "fillOpacity": 0.05},
    name="site cluster",
).add_to(m)

folium.GeoJson(
    proj.trenches.__geo_interface__,
    style_function=lambda f: {"color": "#3b6e8f", "weight": 2, "opacity": 0.7},
    name="trenches",
).add_to(m)

for _, row in proj.fcps.iterrows():
    folium.CircleMarker(
        location=[row.geometry.y, row.geometry.x],
        radius=5, color="#c97f3a", fill=True, fillOpacity=0.9,
        popup=f"FCP {row.get('fcpName', '?')} — {row.get('kmlDescriptionSimple', '')}",
    ).add_to(m)

# overlay the 5 photos with GPS
gps_df = df[df.has_gps].copy()
print(f"Photos placeable from EXIF GPS: {len(gps_df)}")
for _, r in gps_df.iterrows():
    folium.Marker(
        location=[r.gps_lat, r.gps_lon],
        popup=Path(r["path"]).name,
        icon=folium.Icon(color="green", icon="camera", prefix="fa"),
    ).add_to(m)

folium.LayerControl().add_to(m)
m
"""),
    md("""
**What the map shows:** the project (Maria Rain, Carinthia per the cluster description) is a residential FTTH build with 9 buildings, dense local trenching, and a few green camera pins for the only photos we could place automatically. The contrast between 2,983 segments and 5 placeable photos is the entire reason this challenge is hard.
"""),
    md("## 4 · Coverage feasibility — what would 'matching' even look like?"),
    code("""
# Naive: how many segments fall within a given radius of any GPS photo?
buffer_m = 25
photo_pts = gpd.GeoDataFrame(
    geometry=[Point(xy) for xy in zip(gps_df.gps_lon, gps_df.gps_lat)],
    crs="EPSG:4326",
).to_crs("EPSG:31287")
buf = photo_pts.buffer(buffer_m).unary_union
covered = tr_m.geometry.intersects(buf).sum()
print(f"At {buffer_m} m buffer:  {covered:,} / {len(tr_m):,} segments touched by GPS photos ({covered/len(tr_m):.1%})")
"""),
    md("""
Even if we trust the 5 GPS points, they touch a vanishing fraction of segments. Per-photo geo-matching is **not viable at this dataset scale**. The pipeline must accept lot/project as the matching unit and treat per-photo GPS as opportunistic enrichment.
"""),
    md("""
## Takeaways for the pipeline

1. **Segment-level scoring is too granular** for this dataset. Roll up to FCP / lot / project.
2. **Use GeoJSON to define expected evidence locations** (FCP polygons, named lot polygons), not to receive photo positions.
3. **At upload time the user/contractor must declare lot and FCP** — that becomes the geo-anchor, not EXIF GPS.
4. **EXIF GPS, when present, is a Criterion-6 signal** ("GPS consistent with declared site") — it's a consistency check, not a routing input.
5. **`executionState` tells us where photos are required.** Filter to `Documented` segments before declaring coverage gaps.
"""),
]


# ---------- Notebook 3: labelled examples + duplicates ----------
dup_cells = [
    md("""
# 03 — Labelled examples and duplicate detection

**Two questions:**
1. What do the six APG QC criteria look like in practice? (`project-resources/Beispiele/`)
2. How many photos in the dataset are duplicates or near-duplicates of one another?

Why these together: the labelled examples give us anchors for visual classes; perceptual hashing on the same image features is the cheap, deployable baseline for Criterion 5 ("duplicate or reused photo across lots"). Both depend on getting visual representations right.
"""),
    code("""
import sys, warnings
from pathlib import Path
sys.path.insert(0, str(Path.cwd().parent))
warnings.filterwarnings("ignore", category=FutureWarning)

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
import imagehash
from tqdm.auto import tqdm

from src.cache import load_or_build_photo_index

df = load_or_build_photo_index()
ROOT = Path.cwd().parent
EX = ROOT / "project-resources" / "Beispiele"
print("Example folder contents:")
for p in sorted(EX.rglob("*")):
    if p.is_file(): print(" ", p.relative_to(EX))
"""),
    md("## 1 · The labelled examples (Beispiele/)"),
    code("""
def show_grid(paths, title, ncols=4, scale=2.5):
    paths = [Path(p) for p in paths]
    nrows = (len(paths) + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(ncols*scale, nrows*scale*1.2))
    axes = np.atleast_2d(axes)
    for ax in axes.ravel(): ax.axis("off")
    for ax, p in zip(axes.ravel(), paths):
        try:
            im = Image.open(p); im.thumbnail((400, 400)); ax.imshow(im)
            ax.set_title(p.name[:28], fontsize=8)
        except Exception as e:
            ax.set_title(f"ERR {e}", fontsize=7)
    fig.suptitle(title, fontsize=12, y=1.02)
    plt.tight_layout(); plt.show()

# Single-image references
for stem in ["duct_depth.jpg", "duct_sand.jpg", "warnband.jpeg", "bad.jpeg"]:
    p = EX / stem
    if p.exists():
        show_grid([p], stem, ncols=1, scale=4)
"""),
    code("""
# depth folder
depth_paths = sorted((EX / "depth").iterdir())[:12]
show_grid(depth_paths, f"depth/ — {len(list((EX / 'depth').iterdir()))} positives showing trench depth")
"""),
    code("""
# duct folder
duct_paths = sorted((EX / "duct").iterdir())[:12]
show_grid(duct_paths, f"duct/ — {len(list((EX / 'duct').iterdir()))} positives showing duct in trench")
"""),
    md("""
**Observation:** the labelled examples are **positive class only** (and a single `bad.jpeg`). There is no held-out negative set per criterion, no per-photo multi-label annotation, no inter-rater agreement. For the hackathon prototype this is fine — we use these as VLM few-shot anchors or as a tiny eval set. For a production model, we'd need real labels.
"""),
    md("## 2 · Duplicate detection via perceptual hash"),
    code("""
import json
CACHE = ROOT / "data" / "cache" / "phashes.parquet"

def compute_phashes(paths, size=8):
    out = []
    for p in tqdm(paths, desc="phash"):
        try:
            with Image.open(p) as im:
                im.thumbnail((512, 512))
                h = imagehash.phash(im, hash_size=size)
            out.append(str(h))
        except Exception:
            out.append(None)
    return out

if CACHE.exists():
    h_df = pd.read_parquet(CACHE)
else:
    h_df = df[["path"]].copy()
    h_df["phash"] = compute_phashes(df.path.tolist())
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    h_df.to_parquet(CACHE, index=False)
print(f"phashes computed: {h_df.phash.notna().sum():,} / {len(h_df):,}")
"""),
    code("""
# Exact-hash duplicates (Hamming distance == 0)
exact = h_df.groupby("phash").size().sort_values(ascending=False)
exact = exact[exact > 1]
print(f"Distinct phashes:           {h_df.phash.nunique():,}")
print(f"Hashes with >=2 photos:     {len(exact):,}")
print(f"Photos in exact-dup groups: {int(exact.sum()):,}")
print()
print("Top 5 dup groups (size):")
print(exact.head())
"""),
    code("""
# Show the largest duplicate group, side by side
top_hash = exact.index[0]
dup_paths = h_df.loc[h_df.phash == top_hash, "path"].tolist()
print(f"Top group: {len(dup_paths)} photos with phash {top_hash}")
show_grid(dup_paths[:8], f"Largest phash collision group ({len(dup_paths)} photos)", ncols=4)
"""),
    code("""
# Near-duplicates: Hamming distance <= 6 (out of 64) — count by sampling pairs
# Full pairwise is O(N^2) — for ~4k images that's 8M comparisons but cheap on 64-bit ints
hashes_valid = h_df.dropna(subset=["phash"]).reset_index(drop=True)
hash_ints = np.array([int(str(h), 16) for h in hashes_valid.phash], dtype=np.uint64)

def hamming(a, b):
    return bin(int(a) ^ int(b)).count("1")

# Cheap heuristic: bucket by top 16 bits; only compare within bucket
bucket_key = (hash_ints >> 48).astype(np.uint64)
near_pairs = []
threshold = 6
for b in tqdm(np.unique(bucket_key), desc="near-dup buckets"):
    idx = np.where(bucket_key == b)[0]
    for i_pos, i in enumerate(idx):
        for j in idx[i_pos+1:]:
            d = hamming(hash_ints[i], hash_ints[j])
            if d <= threshold:
                near_pairs.append((i, j, d))
print(f"Near-duplicate pairs (hamming <= {threshold}, top-16-bit bucketed): {len(near_pairs):,}")
"""),
    md("""
**Method note:** bucketing by the top 16 bits is a fast prefilter — it misses pairs that differ in those bits but agree elsewhere. For a hackathon dup-flagging baseline it's good enough; production should use a proper LSH or BK-tree. Reported counts are a lower bound.
"""),
    code("""
# Visualise a few near-dup pairs that aren't exact matches
pairs_neq = [(i, j, d) for i, j, d in near_pairs if d > 0][:6]
for i, j, d in pairs_neq:
    pa = hashes_valid.path.iloc[i]; pb = hashes_valid.path.iloc[j]
    show_grid([pa, pb], f"hamming={d}  — visually similar pair", ncols=2, scale=3.5)
"""),
    md("""
## Takeaways for the pipeline

1. **Exact phash collisions exist** in this dataset — these are the easy "duplicate photo reused" cases. A 64-bit phash with strict equality is a defensible first pass.
2. **Near-duplicate detection at hamming ≤ 6** surfaces re-crops / re-shoots of the same subject. Useful for catching contractors who try harder to disguise reuse.
3. **Pair this with file-byte SHA-256** as a parallel signal: identical bytes is 100% confidence duplicate, regardless of visual content.
4. **Cross-lot duplicates are the high-value signal** — same image in lot 1 and lot 2 likely means evidence reuse. This needs the lot label to be reliable, which is `01_dataset_overview` Section 3's open question.
5. **Labelled positives are too few for supervised training.** Plan A is a VLM (e.g., Claude / GPT-4 vision) with the criteria + a few example anchors per criterion; Plan B is a per-criterion small classifier trained on hand-labelled subsets of this corpus.
"""),
]


paths = [
    write("01_dataset_overview.ipynb", overview_cells),
    write("02_geo_coverage.ipynb", geo_cells),
    write("03_examples_and_duplicates.ipynb", dup_cells),
]
for p in paths:
    print("wrote", p)
