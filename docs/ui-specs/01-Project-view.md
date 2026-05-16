# UX Specification: Screen 1 — Project Dashboard

## Context for UI Engineer

This is the landing page of the application. It serves as an overview of all trench documentation projects managed by öGIG.

The primary goal is to allow users to:

- Quickly find existing projects

- Check their high-level status

- Initiate the creation of new projects via a modal popup

---

# 1. Page Layout & Structure (Screen 1)

The page is a clean, grid-based dashboard.

## 1.1 Top Navigation Bar

Contains:

- App logo `öGIG`)

- User profile

- Global search

---

## 1.2 Page Header

Contains:

- Page title: **"Trench Quality Projects"**

- Filtering controls

- Sorting controls

---

## 1.3 Project Grid

A responsive grid displaying:

- Existing project cards

- The **"Add New"** action tile

---

# 2. UI Elements: Project Cards

Each existing project is represented as a clickable card.

**Domain note:** A dashboard **Project** is the same geographic entity as a **cluster** in the planning GeoJSON (`clusterName` on FCP features, boundary from `*_SiteCluster_Polygons.geojson`). The map (Screen 3) opens at this project / cluster level before drilling into FCPs and individual trench images.

## Card Content

### Project Name

Prominent title.

Example:

- `Graz-Waltendorf Phase 1`

---

### Region / State

Subtitle indicating location.

Example:

- `Styria`

---

### Date

Displays:

- Creation date

  **or**

- Last modified date

---

### Photo Count

A small badge or text indicator showing the volume of uploaded data.

**Data note:** This count reflects **upload volume** (e.g. `photo_count` / number of image assets). Map **documentation quality** (green/yellow/red segments) comes from **rolled-up photo analysis**, not from this badge alone.

Example:

- `847 Photos`

---

### Status Indicator

Visual tag showing the current project state.

#### Draft

- Color: Grey

- Meaning: Upload incomplete

#### Analysing

- Color: Blue

- State: Animated

- Meaning: AI processing in progress

#### Complete

- Color: Green

- Meaning: Map view ready for review

---

## Interaction Behaviour

### Completed Project

Clicking anywhere on a completed project card navigates the user directly to:

- **Screen 3 — Map View**

---

### Draft Project

Clicking on a draft project navigates the user to:

- **Screen 2 — File Upload**

This allows the user to resume progress.

---

# 3. UI Elements: "Add New" Action Tile

Positioned as the first card in the grid (top-left) to ensure high visibility.

---

## Design

The tile should include:

- A dashed or visually distinct border

- A large centered `+` icon

- Text label:

```text

Add New Project