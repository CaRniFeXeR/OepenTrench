# UX Specification: Screen 1 — Project Dashboard 

Context for UI Engineer:

This is the landing page of the application. It serves as an overview of all trench documentation projects managed by öGIG. The primary goal is to allow users to quickly find existing projects, check their high-level status, and initiate the creation of new projects via a modal popup.

## 1. Page Layout & Structure (Screen 1)

The page is a clean, grid-based dashboard.

[1.Top](http://1.Top) Navigation Bar: App logo (öGIG), user profile, and global search.

[2.Page](http://2.Page) Header: Title ("Trench Quality Projects") and filtering/sorting controls.

3.Project Grid: A responsive grid displaying project cards and the "Add New" action tile.

## 2. UI Elements: Project Cards

Each existing project is represented as a clickable card.

Card Content:

•Project Name: Prominent title (e.g., "Graz-Waltendorf Phase 1").

•Region/State: Subtitle indicating location (e.g., "Styria").

•Date: Creation or last modified date.

•Photo Count: A small badge or text indicating the volume of data (e.g., "847 Photos").

•Status Indicator: A visual tag showing the current state of the project:

•Draft (Grey) — Upload incomplete.

•Analysing (Blue/Animated) — AI processing in progress.

•Complete (Green) — Map view ready for review.

Interaction:

•Clicking anywhere on a completed project card navigates the user directly to Screen 3 (Map View).

•Clicking on a draft project navigates to Screen 2 (File Upload) to resume progress.

## 3. UI Elements: "Add New" Action Tile

Positioned as the first card in the grid (top-left) to ensure high visibility.

Design:

•A card with a dashed or distinct border.

•A large, centered "+" icon.

•Text: "Add New Project".

Interaction:

•Clicking this tile does not navigate to a new page. Instead, it triggers Screen 1.2 (Add Project file).