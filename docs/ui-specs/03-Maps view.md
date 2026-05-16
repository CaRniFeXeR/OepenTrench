# UX Specification: Screen 3 — Map View (Trench Analysis)

## Context for UI Engineer

This is the core analytical interface of the application. It visualizes AI quality-control results across three progressive levels of detail, designed to feel like navigating Google Maps — from the full **project** (site cluster), drilling into an **FCP** (fiber concentration area), and finally opening an individual **trench image**. The map remains visible and interactive at all levels; the side panel provides contextual detail without replacing the map.

## Domain vocabulary

| Term | Meaning | GeoJSON / data |
| --- | --- | --- |
| **Project** | The entire site cluster; same as dashboard “project” | `*_SiteCluster_Polygons.geojson`; `clusterName` on FCP features (e.g. `CLP20417A`) |
| **FCP** | Sub-area of the project (fiber concentration point / lot) | `*_FCP_Polygons.geojson`, `*_FCPs.geojson` (`fcpName`, `kmlName`, e.g. `F012`) |
| **TrenchImage** | One uploaded field photo and its `PhotoAnalysis` | Image assets + analysis rows |
| **Trenches** | Supporting route geometry (not a drill-down level) | `*_Trenches.geojson` — ~2,983 `LineString` segments in the sample bundle |

Example bundle prefix: `CLP20417A-P1-B00` → `{base}_SiteCluster_Polygons`, `{base}_FCP_Polygons`, `{base}_FCPs`, `{base}_Trenches` (see [`data/example_geojson/`](../../data/example_geojson/)).

**Cluster ≡ Project** in all UX copy unless referring to raw GeoJSON property names.

## 1. Navigation Hierarchy Overview

Screen 3 has three distinct levels of depth. Each level is reached by zooming in or clicking deeper into the map, and exited by clicking outside the panel or pressing a back button.

| Level | Name | Trigger | Map State | Side Panel |
| --- | --- | --- | --- | --- |
| Level 1 | **Project overview** | Default on load | Fit site-cluster bounds; all FCP polygons + full trench network | Static overlay panels (Left, Bottom, Right) |
| Level 2 | **FCP detail** | Click **FCP polygon** or **FCP point** | Zoom to selected FCP; trenches inside; photo markers | FCP summary panel slides in from the right |
| Level 3 | **TrenchImage detail** | Click a **photo marker** or use prev/next in FCP panel | Center on active photo; highlight marker | TrenchImage + `PhotoAnalysis` detail |

**Sub-specifications:**

- [03.1 — FCP Detail (Level 2)](./03.1-fcp-view.md)
- [03.2 — TrenchImage Detail (Level 3)](./03.2-trenchimage-view.md)

## 2. Level 1 — Project Overview

### 2.1 Initial Load State

The map loads bounded and zoomed to the **site cluster polygon** (`*_SiteCluster_Polygons.geojson`). If that file is missing, fall back to the union of FCP polygons and trench geometry. The view also respects uploaded photo positions where available from Screen 2.

### 2.2 Map Elements

**Network nodes (icons):**

- **POP (Point of Presence):** Central network hub — dark blue/purple square with a building icon (from `*_POP.geojson` when present; may be empty).
- **FCP (Fiber Concentration Point):** Distribution hub — solid purple square (`*_FCPs.geojson` points). **Clicking an FCP point or its polygon enters Level 2.**
- **Customer connection:** End customer — small blue circle (trenches with `isConnectedToHome`).

**FCP areas (polygons):**

- Semi-transparent fills from `*_FCP_Polygons.geojson`, labelled by `kmlDescriptionSimple` (e.g. `F012 [81]`). **Primary Level 2 entry target.**

**Route segments (lines):**

Trench lines from `*_Trenches.geojson` are color-coded from rolled-up photo analysis. Documentation expectation: roughly one compliant photo per 5 m of trench length (used for gap analysis, not as the map navigation unit).

| Color | Status | Meaning |
| --- | --- | --- |
| Green | Complete | Compliant photo every 5m and RTK GPS survey available |
| Yellow | Partial | Photos present but quality insufficient or survey not fully compliant |
| Red | Missing | No compliant survey and/or no compliant photos available |

**Trench line interaction at Level 1:** Hover may show a tooltip (segment id, length, status). **Click does not change level** — only FCP polygon/point selection opens Level 2.

**Photo markers at Level 1:** Hidden to avoid clutter (shown from Level 2 onward).

### 2.3 Static Overlay Panels

**Left panel — Network structure legend:**

A floating panel explaining map icons (POP, FCP, customer connection) and a brief model-purpose line: "Automatically identifies trench sections where documentation does not meet the specified requirements."

**Bottom panel — Documentation status summary:**

- **Left side:** Network overview text (e.g. `CLP20417A • 9 FCPs • 19.6 km trenches` — illustrative counts from the sample bundle).
- **Right side:** Horizontal bar chart of total trench length by status (Green / Yellow / Red).

**Right panel — Trench status breakdown:**

Three stacked color blocks:

- **GREEN — Complete:** [X%] of total route length
- **YELLOW — Partial:** [X%] of total route length
- **RED — Missing:** [X%] of total route length

### 2.3.1 Workflow status vs segment colours

Card / project **workflow** states (**Draft**, **Analysing**, **Complete**) describe upload and pipeline progress. **Green / Yellow / Red** trench segments describe **documentation quality** only: they aggregate from **per-photo** analysis (**`PhotoAnalysis.category`**: `green` \| `yellow` \| `red`) and related rules — not from `ProjectStatus`. Keep both concepts separate in APIs and legend copy.

Rollups chain **per TrenchImage → per FCP → per project**, length-weighted over trench geometry where segment lengths are available.

### 2.4 Interaction to Enter Level 2

Clicking an **FCP polygon** or **FCP point** triggers Level 2 (FCP detail). The map smoothly zooms to that FCP and the side panel slides in from the right. See [03.1 — FCP Detail](./03.1-fcp-view.md).
