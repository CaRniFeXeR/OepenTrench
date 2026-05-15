# Problem reasoning — ÖpenTrench / APG construction photo audit

Written after a first pass over `project-resources/` and the three exploratory notebooks. Numbers below are measured, not estimated.

## The challenge in one sentence

Given thousands of construction site photos per project, automatically decide which ones satisfy each of six documentation criteria, which are duplicates or reused across lots, and which segments of the trench network lack adequate evidence — then emit a deficiency report a contractor and an engineer can both act on.

## The six criteria (from the APG brief)

1. Warning tape visible
2. Sand bedding documented before backfilling
3. Side view / trench profile present
4. Trench depth confirmed with visible reference (e.g. ruler)
5. Duplicate or reused photo detected across lots
6. GPS location consistent with declared project site

Each photo gets one of `pass / fail / undetectable` per criterion. Each lot or project gets a completeness rollup.

## What the sample dataset actually looks like

Measured from `project-resources/Fotos/` and `project-resources/geojson/`:

| Property | Value |
|---|---|
| Photos | 3,929 |
| With any EXIF | 17 (0.4%) |
| With GPS EXIF | **5 (0.1%)** |
| Usable date from filename | 3,523 (89.7%) |
| Source = WhatsApp | 99.9% |
| Median resolution | 1200×1600 |
| Trench segments (GeoJSON) | 2,983 (19.6 km total) |
| Median segment length | 4.1 m |
| Segments in state `Documented` | 2,950 (98.9%) |
| Exact-phash duplicate groups | 575 covering 1,277 photos (32.5%) |
| Near-dup pairs (hamming ≤ 6) | 862 additional |

## Constraints that fall out of the data

**1. Per-photo GPS is unavailable in practice.** Production photos arrive via WhatsApp; EXIF is stripped. Five out of 3,929 retained coordinates. The pipeline cannot route photos to trench segments via image metadata alone. Criterion 6 has to be reframed: it is a *consistency check* when GPS happens to be present, not a routing input.

**2. Geo-matching unit is the lot, not the segment.** Median segment is 4.1 m; phone GPS is ±5–15 m even when present. Even with perfect EXIF, segment-level photo↔geometry matching is below the noise floor of consumer GPS. The right unit is *project → lot → FCP*, with segment-level used only to highlight unphotographed sub-routes.

**3. Filename is the most reliable timestamp.** 89.7% of photos have a usable date from `IMG-YYYYMMDD-WAxxxx` or `WhatsApp Image YYYY-MM-DD`. EXIF DateTimeOriginal exists for 5. Build the data model around filename-derived dates and accept that intra-day ordering is lost on WhatsApp raw exports.

**4. The dataset has substantial duplication already.** 1,277 photos (32.5%) share an exact perceptual hash with at least one other photo in the same project. This is the visible tip of Criterion 5 — and a strong hint that contractors already reuse photos within projects, never mind across lots.

**5. The `1_`, `2_`, … filename prefix is unexplained.** 26% of photos have it, distribution is skewed (471 / 471 / 68 / 13 / 2 / 1 / 1), and the rest have nothing. Plausibly a manual lot tag. **Open question for the challenge owner** before we anchor any pipeline logic on it.

## What the visual data tells us (eyeballing 24 random samples)

- Most photos are open trench shots — duct bundles, sand backfill, exposed cable runs.
- A meaningful fraction are wide scene shots (road, house facade) with no visible trench at all.
- Reference photos with a ruler / tape measure are present but uncommon — Criterion 4 (depth confirmed) is the rarest positive.
- Lighting, framing, motion blur, and occlusion (hands, boots in frame) are all common. Models will need to handle real-world noise.

A single end-to-end classifier ("is this a compliant photo?") will not work. Per-criterion detectors or a VLM with structured prompts are the realistic options.

## Recall-first stance

The brief and the user have both emphasised: a missed defect is far costlier than a false alarm. Concretely:

- Set classifier thresholds for **high recall (≥0.9 if achievable) on the failure class**, even at the cost of precision.
- Default `undetectable` to `fail` for reporting purposes, with an "uncertain" tag the engineer can resolve. Forcing review on uncertainty is cheaper than letting a flag through.
- Surface the *evidence* alongside the verdict — the cropped region a detector triggered on, or the VLM rationale — so the engineer can adjudicate in seconds, not minutes. This is what makes recall-first survivable.

## Pipeline sketch (informed by the above)

```
upload  ─►  lot/project declared by user  ─►  per-photo:
                                                 ├─ EXIF + filename → date, GPS-if-present
                                                 ├─ perceptual hash → corpus + cross-lot dup check
                                                 └─ six criteria detectors / VLM → pass/fail/uncertain
                                                                     │
                          rolled up: lot completeness, project rollup ◄
                                                                     │
                                                              deficiency report (md/pdf + map)
```

## Open questions for the challenge owner

1. What does the filename prefix `1_`, `2_`, … represent? Lot? Inspector? Date batch?
2. Is the production submission flow going to preserve EXIF (project plans say "geo-getagged"), or is the WhatsApp pattern in this sample representative?
3. What level of rollup is in the contractor-facing report? Per photo? Per lot? Per project?
4. Is there ground-truth labelling we can use for evaluation, or is the only labelled material the `Beispiele/` examples?
5. For Criterion 4 (depth), is a ruler in frame the only accepted evidence, or does a measurement caption / annotated overlay also count?

## Non-goals for the hackathon prototype

- Production-grade model training. The labelled set is too small.
- Live ingest from a contractor portal. Batch upload via a local UI is enough.
- Multi-tenancy / auth / NDA-grade infra. Documented as production work.

## Next steps

1. Resolve the open questions above (sync with challenge owner).
2. Decide between (a) per-criterion lightweight detectors with hand-labelled subsets and (b) a VLM (Claude / GPT-4 vision) with the six criteria as a structured prompt + few-shot examples from `Beispiele/`. The notebooks contain enough samples to A/B both on a tiny labelled eval set.
3. Build the lot-level rollup and the deficiency report skeleton early — these are independent of the model choice and feed the demo narrative.
