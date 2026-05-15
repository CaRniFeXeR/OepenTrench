# UX Specification: Screen 3 — Map View (Trench Analysis)

## Context for UI Engineer

This is the core analytical interface of the application. It visualizes the AI quality control results across three progressive levels of detail, designed to feel like navigating Google Maps — from a high-level regional overview, drilling down into individual trenches, and finally stepping through photos node by node. The map remains visible and interactive at all levels; the side panel provides contextual detail without replacing the map.

## 1. Navigation Hierarchy Overview

Screen 3 has three distinct levels of depth. Each level is reached by zooming in or clicking deeper into the map, and exited by clicking outside the panel or pressing a back button.

| Level | Name | Trigger | Map State | Side Panel |
| --- | --- | --- | --- | --- |
| Level 1 | Cluster Overview | Default on load | Regional map, full route visible | Static overlay panels (Left, Bottom, Right) |
| Level 2 | Trench Detail | Click on a trench segment or cluster | Map zooms into the selected trench, nodes appear | Side panel slides in from the right |
| Level 3 | Photo Navigation | Click a node on the map or use left/right arrows | Map highlights the active node | Side panel updates to show individual photo detail |

**Sub-specifications:**

- [03.1 — Trench Detail (Level 2)](./03.1-trenchimageview.md)
- [03.2 — Photo Navigation (Level 3)](./03.2-individual_images.md)

## 2. Level 1 — Cluster Overview

### 2.1 Initial Load State

The map loads showing a regional overview automatically bounded and zoomed to fit the full uploaded route network. The view is determined by the GeoJSON and photo GPS coordinates uploaded in Screen 2.

### 2.2 Map Elements

**Network Nodes (Icons):**

- **POP (Point of Presence):** Central Network Hub — dark blue/purple square with a building icon.
- **FCP (Fiber Concentration Point):** Distribution Hub — solid purple square.
- **Customer Connection:** End Customer — small blue circle.

**Route Segments (Lines):**

Trench lines connect the nodes and are color-coded based on AI analysis of the uploaded photos. The rule is one compliant photo required per every 5 metres of trench length.

| Color | Status | Meaning |
| --- | --- | --- |
| Green | Complete | Compliant photo every 5m and RTK GPS survey available |
| Yellow | Partial | Photos present but quality insufficient or survey not fully compliant |
| Red | Missing | No compliant survey and/or no compliant photos available |

### 2.3 Static Overlay Panels

**Left Panel — Network Structure Legend:**

A floating panel explaining the map icons (POP, FCP, Customer Connection) and a brief "Model Purpose" description: "Automatically identifies trench sections where documentation does not meet the specified requirements."

**Bottom Panel — Documentation Status Summary:**

- **Left side:** Network overview text (e.g., "1 POP • 4 FCPs • 32 Connections").
- **Right side:** A horizontal bar chart showing the percentage breakdown of total trench length by status (Green / Yellow / Red).

**Right Panel — Trench Status Breakdown:**

Three stacked color blocks showing:

- **GREEN — Complete:** [X%] of total route length
- **YELLOW — Partial:** [X%] of total route length
- **RED — Missing:** [X%] of total route length

### 2.4 Interaction to Enter Level 2

Clicking on any trench segment line or cluster on the map triggers the transition to Level 2 (Trench Detail). The map smoothly zooms into the selected trench area and the side panel slides in from the right. See [03.1 — Trench Detail](./03.1-trenchimageview.md).
