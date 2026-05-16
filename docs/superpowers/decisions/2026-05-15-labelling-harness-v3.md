# Labelling Harness v3 — Decision Journal

**Spec:** `docs/superpowers/specs/2026-05-15-labelling-harness-v3-design.md`
**Status:** Open
**Branch/worktree:** `feat/labelling-harness-v3`

## Task Outline

The following tasks are dispatched through `subagent-driven-development`. Granularity target: 30 min – 2 hr each. Dependencies (`deps`) are task ids that must complete first; `—` means independent.

1. **Update class schema + inspector** — scope: bump `data.yaml` to 4 classes (duct, ruler, whitepaper, sitetag); extend `scripts/inspect_labels.py` to read class names from `data.yaml` and accept `--run <dir>` / `--data-yaml <path>`, preserving v2 behaviour when no flags given; spec anchor: §6.1, §11 ("Files to modify"), §12 AC #1, #2, #10; deps: —.

2. **Local dataclasses + config loader** — scope: `src/oepentrench/labelling/{__init__,base,config}.py` (`Detection`, `LabelOutput`, `Labeller` ABC, `LabellerConfig` Pydantic model, YAML→config loader, validation errors mapped to `ConfigError`); deps in `pyproject.toml`: `httpx`, `pyyaml`, `pydantic`, plus `respx` in dev; spec anchor: §4.1, §5.5, §6.5, §11; deps: —.

3. **Remote labeller + runner** — scope: `src/oepentrench/labelling/{remote_labeller,runner}.py`. `RemoteVlmLabeller` is an httpx client to `/detect` with retry/backoff per error taxonomy; `runner` iterates a manifest, calls the labeller serially, writes per-image outputs atomically, supports `--limit` / `--batches` / `--image-path` (ad-hoc), handles intra-run resume, emits `run_manifest.json` on completion or interrupt; spec anchor: §3, §5.5, §6.2, §6.3, §6.4, §7, §8; deps: 2.

4. **Hybrid skeleton** — scope: `src/oepentrench/labelling/hybrid_labeller.py` — importable `HybridLabeller(Labeller)` class whose `label()` raises `NotImplementedError`. Exists for ABC contract tests; not selectable via config this session. Spec anchor: §4.1 hybrid row, §5.5; deps: 2.

5. **Compare tool** — scope: `src/oepentrench/labelling/compare.py` + `scripts/compare_runs.py`. Greedy per-class IoU matching between two run dirs; emits per-photo agreement JSON with the summary block; optional `--fiftyone` flag opens side-by-side. Spec anchor: §6.6, §13 (greedy IoU matching gap), §11; deps: 2.

6. **CLI entry point** — scope: `scripts/label.py` — orchestrates config load, manifest filter, labeller instantiation, runner invocation, exit code mapping per §7; supports all flags from §5.6 including `--image-path` and `--health-check`. Spec anchor: §5.6, §7, §11; deps: 2, 3.

7. **Local tests** — scope: `tests/labelling/{test_config,test_bbox,test_resume,test_compare,test_remote_integration}.py`. Unit + mocked integration per §10; `respx` for httpx mocking. `pytest tests/labelling/ -q` must exit 0. Spec anchor: §10, §12 AC #8; deps: 2, 3, 4, 5.

8. **VM scaffold + Grounding DINO adapter** — scope: `~/repos/vision/` on `threenicorn`: `pyproject.toml` (uv-managed, torch cu128, transformers≥4.45, fastapi, uvicorn), `Makefile` with targets `grounding-dino|qwen-vl|owlv2|florence2|t-rex2|health|stop` (only `grounding-dino` and `health`/`stop` functional this session; others bind to stub adapters that fail-load cleanly), `server/main.py` FastAPI app with `/detect`, `/health`, `/info`, `server/schema.py` Pydantic models, `server/adapters/{base,grounding_dino,qwen_vl,owlv2,florence2,trex2}.py` (only `grounding_dino` functional), `tests/test_health.sh`, `README.md`. The implementer SSHes to the VM and writes files there directly (or rsyncs from local). Spec anchor: §4.4, §4.5, §5.1–§5.4, §11, §12 AC #4; deps: —.

9. **Operator runbook** — scope: `docs/labelling-harness.md` — one-page document covering: SSH tunnel command, `make` workflow for VM model selection, corpus rsync steps, the operator-mediated Claude run workflow that produces `labelling/runs/claude-opus_<ts>/` in the same on-disk shape, hybrid-mode-next-session sketch. Spec anchor: §3 (operator paragraph), §12 AC #3; deps: 8 (so VM workflow can be documented as it actually exists).

After these eight tasks complete and pass per-task review, the remaining acceptance criteria (AC #4 tunneled health, AC #5 Beispiele round-trip, AC #6 batch_00 round-trip, AC #7 compare-against-v2 diff shown to user) are validated **interactively in the main Claude Code session** as operator gates — not via subagent dispatch — because they require live SSH and user judgment on the diff.

### Dependency graph

```
1 ──(no deps)
2 ──(no deps)
3 ── 2
4 ── 2
5 ── 2
6 ── 2, 3
7 ── 2, 3, 4, 5
8 ──(no deps)
9 ── 8
```

Parallelisable starting points: 1, 2, 8 — dispatched together.

## Logging Rules (copied into implementer instructions)

An entry MUST be appended to this file whenever the implementer:
- Chooses between viable options not settled by the spec
- Fills a §13 Known Gaps item from the spec
- Picks a name for a public interface, error class, config key, or persistence field
- Selects a dependency, library, or algorithm where alternatives exist
- Decides on an error-handling policy for a case the spec's §8 didn't fully pin down
- Chooses a concurrency, locking, or retry strategy
- Departs from an existing convention in the codebase
- Trims or defers scope the spec listed (and justifies the defer)

An entry is NOT required for:
- Pure mechanics dictated by language, linter, or existing convention
- Renames/refactors strictly internal to a function body
- Whitespace, import ordering, formatting
- Literal transcription from spec §5 / §6 signatures and contracts

When in doubt: log it. A spurious log entry costs nothing; a missing one costs the audit.

## Entry Schema Reminder

```markdown
### D-<NNN>: <short noun phrase>

- **Timestamp:** YYYY-MM-DD HH:MM (local)
- **Task:** Task <N> — <name>
- **Trigger:** <what surfaced the decision>
- **Spec anchors:** §<N.x>, §<M.y>
- **Options considered:**
  1. <option A>
  2. <option B>
- **Chosen:** Option <X>
- **Reasoning:** <2–6 sentences>
- **Out-of-scope alternatives deferred:** <what we did NOT do and why>
- **Affected files:** `<path>`, `<path>`
- **Commit:** <sha or "pending">
- **Supersedes:** <D-XXX if revises an earlier decision, else "—">
```

Minimum bar: 2 options, 1 chosen, explicit reasoning.

## Entries

<!-- entries appended below, newest last -->

### D-001: Class name loading strategy (eager vs. lazy)

- **Timestamp:** 2026-05-16 11:00 (local)
- **Task:** Task 1 — Update class schema + inspector
- **Trigger:** `inspect_labels.py` needed to replace the hardcoded `CLASS_NAMES` tuple with runtime-loaded names; question of when to load.
- **Spec anchors:** §4.2 (`inspect_labels.py` row), §12 AC #2, §13 (extend-in-place gap)
- **Options considered:**
  1. Eager load at startup: parse `data.yaml` once in `main()` before anything else, pass `class_names` as a parameter to `yolo_line_to_detection`, `build_samples`, and `pick_layout`. Simple call graph; the list is available to every caller without module-level state.
  2. Module-level lazy singleton: parse `data.yaml` on first call to a `get_class_names()` function, cache in a module global. Reduces parameter threading but introduces mutable global state and complicates testing.
  3. Module-level constant (loaded at import time): replaces `CLASS_NAMES = (...)` with `CLASS_NAMES = load_class_names(_DEFAULT_DATA_YAML)`. Simple, but imports `yaml` at module level and causes side-effects (file I/O) on import, which is bad for unit testing and for callers that want to override the path.
- **Chosen:** Option 1 (eager load in `main()`, passed as parameter)
- **Reasoning:** `main()` already owns argument parsing, so it is the right place to resolve the `--data-yaml` path and load class names once. Passing the list as a parameter to helpers is idiomatic Python, keeps functions pure and testable, and avoids module-level side effects. The list is small (N ≤ 10), so repeated access cost is negligible.
- **Out-of-scope alternatives deferred:** Option 3 (import-time load) was common in the v2 codebase for small constants but is not used here because the path is now a CLI argument. Option 2 deferred indefinitely — no reason to add global state given the simplicity of option 1.
- **Affected files:** `scripts/inspect_labels.py`
- **Commit:** pending
- **Supersedes:** —

---

### D-002: pyyaml as a runtime vs. optional dependency

- **Timestamp:** 2026-05-16 11:05 (local)
- **Task:** Task 1 — Update class schema + inspector
- **Trigger:** `inspect_labels.py` now calls `yaml.safe_load()` to parse `data.yaml`. `pyyaml` was not in `pyproject.toml`; spec §11 lists it as a dep to add.
- **Spec anchors:** §11 ("Files to modify" — pyproject.toml), §13 (pyyaml-staging gap)
- **Options considered:**
  1. Add `pyyaml>=6.0,<7` to `[project.dependencies]` (main runtime deps). Universally available; no extra install step for any user of the package.
  2. Add `pyyaml` only to the `[inspect]` optional group, alongside `fiftyone`. Minimises the mandatory dep surface but requires remembering to install extras for a dep that will also be needed by Task 2 (`config.py`) and `scripts/label.py`.
  3. Implement a stdlib-only YAML parser (regex over the `names:` block). Avoids a new dep entirely but is fragile and hard to maintain against arbitrary YOLO `data.yaml` variations.
- **Chosen:** Option 1 (main runtime dep)
- **Reasoning:** Spec §11 explicitly lists `pyyaml` as a runtime dep to add to `pyproject.toml`. Task 2 (`config.py`) and later tasks (`label.py`, `compare_runs.py`) will also need it; putting it in main deps now avoids repeated edits. `pyyaml` is a small, stable library with no binary extension — there is no cost to making it universal.
- **Out-of-scope alternatives deferred:** Option 3 (stdlib parser) deferred permanently — pyyaml handles YOLO's quirks (integer keys, flow style) that a naive regex would miss. Option 2 considered but rejected because the dep will be needed in non-inspect contexts (Task 2).
- **Affected files:** `pyproject.toml`
- **Commit:** pending
- **Supersedes:** —

---

### D-003: Invalid class-id handling (drop with WARN vs. error)

- **Timestamp:** 2026-05-16 11:08 (local)
- **Task:** Task 1 — Update class schema + inspector
- **Trigger:** `yolo_line_to_detection` formerly checked `cls_id not in (0, 1)`; needed a policy for class ids that fall outside the loaded class list (e.g., a v2 label file opened against a 4-class data.yaml — no such ids exist, but the inverse scenario, a future v5 label against a 4-class data.yaml — is possible).
- **Spec anchors:** §8 (error taxonomy, `MalformedResponse` row), §13 (extend-in-place gap)
- **Options considered:**
  1. Warn and drop: print a `warn:` line to stderr with the offending id, return `None`, continue. Forward-compatible; a v2 label opened against a 4-class data.yaml works fine (ids 0/1 are valid; ids 2/3 absent — no warning because they are in range).
  2. Hard error: raise an exception or call `sys.exit()`. Safe but breaks inspection if even one .txt file has a stale id; not useful for a browse-and-inspect tool.
  3. Silent drop: return `None` with no warning. Loses debuggability; an operator would not know why a bbox disappeared.
- **Chosen:** Option 1 (warn and drop)
- **Reasoning:** The inspector is a browse tool, not a validator. Dropping an unknown bbox with a visible warning keeps the dataset loadable while surfacing the anomaly to the operator. This matches the `MalformedResponse` handling in §8 (per-image WARN, continue). It also keeps the behaviour forward-compatible: v2 labels (ids 0/1 only) pass without any warning when opened against the 4-class list.
- **Out-of-scope alternatives deferred:** Option 2 (hard error) not appropriate for a browser; option 3 (silent drop) rejected because it hides real data quality issues.
- **Affected files:** `scripts/inspect_labels.py`
- **Commit:** pending
- **Supersedes:** —

---

### D-004: FiftyOne default_classes source for --run runs

- **Timestamp:** 2026-05-16 11:10 (local)
- **Task:** Task 1 — Update class schema + inspector
- **Trigger:** When `--run <dir>` is given, the dataset's `default_classes` must be set. Question: use the global `data.yaml` or look for a per-run `data.yaml` inside the run dir.
- **Spec anchors:** §3 (architecture overview — one global `data.yaml`), §12 AC #2, open question in §14 Q2
- **Options considered:**
  1. Always use the global `data.yaml` (resolved via `--data-yaml` or the default `DATASET_ROOT/data.yaml`). Consistent with §14's default: "one global `data.yaml`; revisit if the class set ever forks per profile."
  2. Look for a `data.yaml` inside the run dir first; fall back to global. Future-proof if a later session ships per-run `data.yaml` files, but adds complexity now for a feature deferred to a later session.
  3. Hardcode the class list in the `--run` code path. Not viable — defeats the whole point of loading from data.yaml.
- **Chosen:** Option 1 (global data.yaml only)
- **Reasoning:** Spec §14 open question 2 explicitly says "one global `data.yaml`; revisit if the class set ever forks per profile." No per-run data.yaml is written by the v3 runner this session, so option 2 would silently fall back to option 1 in every real case, adding dead code. Deferring to the next session if per-run class sets ever diverge.
- **Out-of-scope alternatives deferred:** Option 2 deferred to next session (per spec §14 Q2). Option 3 rejected — it regresses the whole data-yaml-driven design.
- **Affected files:** `scripts/inspect_labels.py`
- **Commit:** pending
- **Supersedes:** —

---

### D-005: Stats block generalisation strategy

- **Timestamp:** 2026-05-16 11:12 (local)
- **Task:** Task 1 — Update class schema + inspector
- **Trigger:** The v2 stats block had hardcoded lines for `duct` and `ruler`. With N classes loaded from data.yaml, the block needs to be generic.
- **Spec anchors:** §4.2 (`inspect_labels.py`), §12 AC #2
- **Options considered:**
  1. Loop over `class_names` list, emit one line per class using `dataset.match(fo.ViewField("predictions.detections.label").contains(cls_name))`. Scales to any N classes; identical query pattern per class; preserves the "with X bbox(es)" format.
  2. Keep the hardcoded `n_duct` / `n_ruler` variables and add two more hardcoded variables for `whitepaper` / `sitetag`. Does not scale; breaks every time the class set changes.
  3. Compute a single aggregation and format from it. FiftyOne does not expose a single aggregation that returns per-label counts directly from a Detections field in a single call without a custom evaluation; the per-class `.match()` loop is idiomatic.
- **Chosen:** Option 1 (loop over class_names)
- **Reasoning:** Direct extension of the v2 pattern, scales to N classes, and requires no FiftyOne API change. The format of each line is identical to v2 for the two existing classes, so no backward-compat damage to operators who parse the output.
- **Out-of-scope alternatives deferred:** Option 2 rejected as it does not satisfy AC #2. Option 3 deferred — FiftyOne's aggregation API would need research for no practical gain at this scale.
- **Affected files:** `scripts/inspect_labels.py`
- **Commit:** pending
- **Supersedes:** —

---

### D-006: `src/labelling/` (flat) instead of `src/oepentrench/labelling/` (nested)

- **Timestamp:** 2026-05-16 12:00 (local)
- **Task:** Task 2 — Local dataclasses + config loader
- **Trigger:** Spec §4.1 / §11 names the local package `src/oepentrench/labelling/`, but the existing repo uses a flat `src/` layout (`src/cache.py`, `src/geo.py`, `src/photos.py`; `top_level.txt` = `src`; existing scripts import as `from src.cache import …`). The nested path does not exist on disk.
- **Spec anchors:** §4.1 (component file paths), §11 ("Files to create" — local section)
- **Options considered:**
  1. Restructure the entire repo to `src/oepentrench/<module>/` (move `src/cache.py` → `src/oepentrench/cache.py`, update all imports in `scripts/build_notebooks.py`, update `pyproject.toml`'s `packages.find`, rebuild egg-info). Matches the spec literally but spreads the change across files unrelated to T2.
  2. Use `src/labelling/` for the harness — flat, matches existing convention (`src/cache.py`, `src/photos.py`). Imports inside become `from src.labelling.base import …`, parallel to the existing `from src.cache import …`. The spec's path becomes a deviation, logged here.
  3. Create only `src/oepentrench/labelling/` while leaving the other modules at `src/`. Two different layouts in one repo, asymmetric, confusing.
- **Chosen:** Option 2 (`src/labelling/`).
- **Reasoning:** The spec's path was inherited from a generic project template; the actual repo has a flat `src/` layout, and switching layouts mid-flight is outside T2's scope. Convention-following keeps the diff narrow and avoids breaking the existing `scripts/build_notebooks.py` imports. The audit can compare on responsibility, not on literal path strings — the spec's §4.1 anchors all map cleanly to `src/labelling/<file>.py`.
- **Out-of-scope alternatives deferred:** Renaming the package to `oepentrench` at the project's leisure; global refactor, does not block this feature.
- **Affected files:** `src/labelling/__init__.py`, `src/labelling/base.py`, `src/labelling/config.py`
- **Commit:** pending
- **Supersedes:** —

### D-007: `Detection` / `LabelOutput` as dataclasses, not Pydantic models

- **Timestamp:** 2026-05-16 12:05 (local)
- **Task:** Task 2 — Local dataclasses + config loader
- **Trigger:** Choice of representation for the per-image data carriers. The harness uses Pydantic for the YAML config; the per-image objects could also be Pydantic.
- **Spec anchors:** §5.5 (Detection / LabelOutput shown as `@dataclass`)
- **Options considered:**
  1. Pydantic v2 `BaseModel` for both — runtime validation on every `Detection(...)` construction; catches bbox values outside [0,1] at creation time; bigger import surface and slower instantiation.
  2. `@dataclass` for both — matches the spec's exact wording; no per-instance validation; bbox normalisation responsibility sits with the labeller that constructs them.
  3. `pydantic.dataclasses.dataclass` — middle ground, validates fields but stays dataclass-shaped.
- **Chosen:** Option 2 (stdlib `@dataclass`).
- **Reasoning:** The spec explicitly writes these as `@dataclass`. Bbox-validity is the labeller's invariant — it has the image dimensions and the raw model output; pushing that check into the data class would either be redundant or run at the wrong layer. Pydantic adds dependency weight inside hot loops. Sticking to dataclasses also keeps `LabelOutput.detections: list[Detection]` straightforward.
- **Out-of-scope alternatives deferred:** Adding lightweight bbox-bounds assertions inside `RemoteVlmLabeller` (T3); that's where the invariant belongs.
- **Affected files:** `src/labelling/base.py`
- **Commit:** pending
- **Supersedes:** —

### D-008: Pydantic `extra="forbid"` for `LabellerConfig`

- **Timestamp:** 2026-05-16 12:10 (local)
- **Task:** Task 2 — Local dataclasses + config loader
- **Trigger:** Pydantic v2 default allows unknown fields silently. A YAML typo (`prompt:` instead of `prompts:`) would be ignored and the runner would later fail mid-loop with a misleading "missing prompts" error.
- **Spec anchors:** §6.5 (config schema), §8 (`ConfigError` mapped to exit 2 at startup)
- **Options considered:**
  1. Default Pydantic behaviour — extra fields ignored. Simple but allows silent typos.
  2. `extra="forbid"` — any unknown field raises `ValidationError` at load time. Catches typos immediately, maps to `ConfigError` and exit 2 per §8.
  3. `extra="allow"` — extra fields kept but not validated. Worst of both — easy to add fields the code never reads.
- **Chosen:** Option 2 (`extra="forbid"`).
- **Reasoning:** `ConfigError` exists specifically to abort at startup on invalid YAML (§8). Forbidding unknown fields is the natural extension of that — config typos are exactly the class of error this taxonomy is meant to catch. Cost is one line of config (`model_config = ConfigDict(extra="forbid")`) and slightly stricter YAML; benefit is zero silent-typo bugs at hackathon pace.
- **Out-of-scope alternatives deferred:** Per-field aliasing for backwards compatibility — no prior config schema to be compatible with.
- **Affected files:** `src/labelling/config.py`
- **Commit:** pending
- **Supersedes:** —

### D-009: Cross-key validation of `prompts` and `per_class_threshold` against `classes`

- **Timestamp:** 2026-05-16 12:12 (local)
- **Task:** Task 2 — Local dataclasses + config loader
- **Trigger:** `LabellerConfig.classes` is the source of truth for which classes a run targets. `prompts` and `per_class_threshold` are keyed by class name and could drift from `classes` (typo, missing key, extra key). Pydantic's per-field validation cannot catch this on its own.
- **Spec anchors:** §6.5 (config schema)
- **Options considered:**
  1. Don't validate — let the runner discover at request-build time (`KeyError` on `prompts[cls]`). Cheap but fails late, mid-run.
  2. `@model_validator(mode="after")` that asserts `set(prompts.keys()) == set(classes) == set(per_class_threshold.keys())`. Fails fast at config load with a clear message.
  3. Make `prompts` and `per_class_threshold` optional and fall back to a default if a class key is missing — silently masks misconfiguration.
- **Chosen:** Option 2 (model-level cross validation).
- **Reasoning:** `ConfigError` at startup is strictly better than a `KeyError` 20 photos into a run. The validator also catches the opposite direction (a prompt for a class not in `classes`) which is harder to spot by eye. Same place catches threshold bounds (`[0,1]`), `iou_nms` bounds, `timeout_seconds > 0`, `retries ≥ 0`, `max_detections_per_class ≥ 1` — all invariants the spec implies but doesn't explicitly assert.
- **Out-of-scope alternatives deferred:** Validating class names against `data.yaml` from inside the config loader — that crosses module boundaries; the runner can do that check at startup if needed.
- **Affected files:** `src/labelling/config.py`
- **Commit:** pending
- **Supersedes:** —
