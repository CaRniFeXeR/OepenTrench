# UX Specification: Screen 2 — Project Creation & File Upload

## Context for UI Engineer

This screen handles the creation of a new fiber trench documentation project. The core technical and UX challenge is managing the bulk upload of up to 1,000 geotagged field photos alongside a GeoJSON route file. The UI must keep the user informed during long uploads, validate GPS metadata in real-time, show a live preview of the map being built, and communicate waiting time in a human and friendly way.

## 1. Page Layout & Structure

The page is divided into two main columns once an upload begins:

- **Left Column (Upload Controls):** Project header, photo upload zone, GeoJSON upload zone, and action footer.
- **Right Column (Live Map Preview):** A real-time preview of Screen 3 that builds up as photos and GeoJSON are processed. This column is hidden or shows a placeholder before any upload begins.

On smaller screens, the two columns stack vertically (upload controls on top, map preview below).

## 2. Section Details & Interactions

### 2.1 Project Header

A clean form section at the top of the left column.

**UI Elements:**

- **Project Title Input:** Free text field (e.g., "Route B — Graz-Waltendorf Phase 1"). Required.
- **Region/State Selector:** Dropdown menu to assign the project to a geographic area in Austria. Required.
- **Date Field:** Auto-filled with today's date, editable.
- **Import Button (Secondary):** "Import from external tool" (e.g., Jira, MS Project). Opens a modal or triggers an API sync (placeholder for now).

### 2.2 Photo Upload Zone

Designed for bulk ingestion of 1 to 1,000+ photos.

**Default State:** A large drag-and-drop area with the following text:

- **Primary:** "Drag and drop photos or folders here, or click to browse."
- **Secondary:** "Supported formats: JPG, JPEG, PNG, HEIC. Max 1,000 files per batch."

**Pre-Upload State (File Selection):** Once files are dropped or selected, show a preview count before upload begins (e.g., "847 photos selected") and a "Start Upload" button.

**Active Upload State:** Once upload begins, the drag-and-drop area transitions into a progress section. The following elements are shown:

| Element | Description |
| --- | --- |
| Overall Progress Bar | Visual bar with percentage (e.g., "312 / 847 — 37%") |
| Time Estimate | Dynamic text: "~4 min remaining" |
| Current File | Name of the file currently being processed |
| Pause Button | Pauses the upload without losing progress |
| Cancel Button | Triggers a confirmation dialog: "Cancel upload? Files already uploaded will be kept." |

**Friendly Wait Message:** Once the upload is underway and the estimated time exceeds 1 minute, display a rotating set of friendly messages below the progress bar to reduce perceived wait time. Examples:

- "Uploading takes a while — let's take a coffee break! ☕"
- "Still going… your trench map is being built in the background."
- "Large batch detected — sit tight, we're processing every photo."
- "Almost there — good things take time."

These messages should rotate every 15–20 seconds with a gentle fade transition.

**Real-Time GPS Metadata Validation:** As each photo uploads, the system checks for EXIF GPS data and displays live counters below the progress bar:

- "GPS data found: [Count] ✓" (Green)
- "Missing GPS: [Count] ✗" (Red/Orange)

If photos lack GPS data, a collapsible warning list appears: "The following [Count] photos have no GPS data and cannot be mapped. You may still save the project, but these photos will not appear on the route." The user can choose to remove the flagged photos or keep them with a note.

**Post-Upload Summary State:** Once all photos finish uploading, the progress bar is replaced by a clean summary showing: total uploaded, valid GPS count, missing GPS count, and any duplicate file names detected (with an option to keep or skip duplicates).

### 2.3 GeoJSON Upload Zone

A dedicated section below the photo upload zone for the route file.

**Default State:** A drag-and-drop area or button specifically for the `.geojson` file.

**Missing File Warning (Persistent):** If no GeoJSON is uploaded, display a prominent yellow warning banner:

> ⚠ GeoJSON route file is missing. The map view cannot be generated until this file is added. You can upload it now or return to this project later.

**Uploaded State (Success):** Display a green confirmation (e.g., "✓ Route file loaded — 12.4 km, 6 segments detected"). Optionally show a mini static map thumbnail of the route line to confirm the correct file was uploaded.

### 2.4 Live Map Preview (Right Column)

This is the most important new element of the upload experience. As photos and GeoJSON are processed, the right column shows a live, building preview of Screen 3.

**States of the Preview Panel:**

| State | What Is Shown |
| --- | --- |
| Before any upload | A grey placeholder with text: "Your map will appear here as files are uploaded." |
| GeoJSON uploaded, photos processing | The route skeleton appears as a grey/neutral line on the map. Segments begin turning Green, Yellow, or Red as photos are matched and validated. |
| Upload in progress | The map animates — segments light up progressively as each batch of photos is geo-matched. A subtle pulsing animation on the route line indicates active processing. |
| Upload complete | The full color-coded map is shown. The preview panel displays a visible "View Full Map →" button or becomes fully clickable. |

**Clickable State (Post-Upload):** Once the upload and processing are complete, the entire map preview panel becomes an active, clickable element. Clicking it navigates the user directly to Screen 3 (Map View). A clear call-to-action overlay appears on hover: "Open Full Map View →".

If GeoJSON is missing: The preview panel shows only the uploaded photo GPS points as scattered dots on a map, with a note: "Upload GeoJSON to see the full route map."

### 2.5 Action Footer

Sticky or bottom-aligned controls for saving the project.

| Button | State & Behavior |
| --- | --- |
| "Save Draft" (Secondary) | Always active once at least a title is entered. Saves the project in an incomplete state. |
| "Save & Analyse" (Primary) | Disabled if GeoJSON is missing or upload is still in progress. Active only when both photos (with valid GPS) and GeoJSON are successfully uploaded. Triggers the AI pipeline and navigates to Screen 3. |

A status indicator sits next to the buttons: "Ready to analyse ✓" or "Missing GeoJSON — map cannot be generated ⚠".

## 3. Error Handling & Edge Cases

- **Connection Drop:** Show a non-blocking toast notification: "Upload paused — connection lost. We'll retry automatically." Do not clear progress.
- **Unsupported File Type:** Flag immediately with the file name and reason (e.g., "image_01.pdf is not a supported image format").
- **File Size Limit Exceeded:** Warn the user before the upload begins, not after.

## 4. Developer Notes for Cursor / AI Assistant

- **Two-Column Layout:** Use CSS Grid with a responsive breakpoint. On desktop, left column is ~40% width and right column (map preview) is ~60%. On tablet/mobile, stack vertically.
- **Live Map Preview:** The map preview in the right column should use the same mapping component as Screen 3 (Mapbox GL JS / Leaflet / Google Maps). It should accept incremental GeoJSON feature updates as photos are processed, re-rendering segments as their status is determined. This requires a WebSocket or polling connection to the backend processing pipeline.
- **Friendly Wait Messages:** Implement as a rotating array of strings with a CSS fade-in/fade-out transition (opacity 0 → 1 → 0 over 15–20 second intervals). Trigger only when estimated remaining time exceeds 60 seconds.
- **Reusable Components:** The progress bar, drag-and-drop zones, and map preview panel should all be built as reusable components.
- **EXIF Parsing:** Ensure the frontend or a lightweight backend service can parse EXIF data quickly during the upload stream to power the real-time metadata validation UI.
- **State Management:** The "Save & Analyse" button and the map preview clickable state are both strictly dependent on the presence of a valid GeoJSON file. Ensure this dependency is clearly mapped in the state logic.
