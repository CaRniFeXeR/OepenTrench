# Photo documentation category

Canonical rules for per-photo documentation quality (`PhotoDocumentationCategory`). This drives map markers, project image filters, and rollup statistics. It is **not** project workflow status (`ProjectStatus`).

## Categories

| API value | User label | Rule |
|-----------|------------|------|
| `green` | Good | **All** of: `has_duct`, `has_ruler`, `is_in_domain`, `gps_matches_route` are true **and** `has_gdpr_problems` is false |
| `red` | Failed | **Any** of: `is_duplicated` is true, `gps_matches_route` is false, **or** `is_in_domain` is false |
| `yellow` | Warning | Everything else (partial documentation, privacy flags, missing duct/ruler, etc.) |

Evaluation order: **Failed** first, then **Good**, else **Warning**.

## Automated vs effective values

| Concept | Meaning |
|---------|---------|
| **Automated fields** | Pipeline output on `PhotoAnalysis` (`has_duct`, `has_ruler`, …). Updated only by (re-)analysis. |
| **`category`** | Automated tier from automated fields only. Recomputed on analyze; **never** changed by human review. |
| **Reviewer overrides** | Optional `reviewer_*` booleans. `null` = use automated value. |
| **Effective value** | `reviewer_<field> ?? <automated field>` for each criterion used in categorization. |
| **`effective_category`** | `reviewer_override_category` if set, else category computed from **effective** values. |
| **`reviewed_at`** | Set when a human approves/reviews the photo (warning queue workflow). |

## Human review workflow

Reviewers typically work through **Warning** photos (`yellow`) that are not yet reviewed (`reviewed_at` is null).

On approve they may:

1. **Confirm** automated results (no field overrides) — only sets `reviewed_at`.
2. **Override** individual criteria (e.g. force `has_ruler` false when the model was wrong).
3. **Force category** via `reviewer_override_category` (optional sign-off on Good/Failed without changing fields).

After review, map and list UIs use **`effective_category`** and effective field values for display.

## Re-analyze

Running analyze again **clears** all `reviewer_*` overrides, `reviewer_override_category`, and `reviewed_at`, then recomputes automated fields and `category`.

## Implementation

- Pure logic: [`src/api/helpers/photo_documentation_category.py`](../src/api/helpers/photo_documentation_category.py)
- Persistence: [`PhotoAnalysis`](../src/api/models.py)
- Review API: `PATCH /projects/{project_id}/images/{asset_id}/analysis`
