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

---

### D-010: `MalformedResponseError` writes empty output, `LabellerError` writes nothing

- **Timestamp:** 2026-05-16 13:00 (local)
- **Task:** Task 3 — Remote labeller + runner
- **Trigger:** Spec §8 says "MalformedResponse → per-photo WARN; emit empty detection list for that image; record in `run_manifest.errors[]`; continue" and "LabellerError (after retries) → log + skip + record". Both end up in `errors[]` but the on-disk side-effects differ. The data carriers (`LabelOutput`) have no nullability or error markers, so the labeller must signal the distinction via the exception type.
- **Spec anchors:** §8 (error taxonomy rows), §6.3 (meta JSON shape — needs `image_quality` field), §7 (resume policy: skip when both files exist)
- **Options considered:**
  1. Single `LabellerError` for both, with the runner inspecting message strings or attributes. Fragile and message-format-coupled.
  2. Add a nullable `error_kind` field to `LabelOutput` and have the labeller always return one. Bloats the success type with a never-set field in the common case.
  3. Subclass: `MalformedResponseError(LabellerError)`. Runner catches the subclass specifically: writes empty `<stem>.txt` and a stub `<stem>.json` with `image_quality: "malformed_response"`, increments errors, does NOT increment `images_failed`. Catches plain `LabellerError` separately: increments `images_failed`, writes no files.
- **Chosen:** Option 3.
- **Reasoning:** Clean exception hierarchy maps directly to the spec's two-row distinction. Empty `<stem>.txt` for malformed responses unblocks resume per §7 — re-running with the same config skips the image rather than retrying a request that won't change. Plain `LabellerError` (e.g., 5xx after retries) leaves no files, so re-run will retry the request once the operator fixes whatever caused it. Both still land in `run_manifest.errors[]` with distinct `kind` strings for forensics.
- **Out-of-scope alternatives deferred:** A `Retry-After`-aware backoff for 429 responses; out of scope at hackathon scale.
- **Affected files:** `src/labelling/remote_labeller.py`, `src/labelling/runner.py`
- **Commit:** pending
- **Supersedes:** —

### D-011: Retry classification (which status codes / exceptions are retryable)

- **Timestamp:** 2026-05-16 13:05 (local)
- **Task:** Task 3 — Remote labeller + runner
- **Trigger:** Spec §8 names `LabellerError transient` for "5xx, 429, `httpx.TimeoutException`, `httpx.ConnectError`" but does not enumerate the exact 5xx set, nor where to put `RemoteProtocolError` / `ReadError` / `WriteError`.
- **Spec anchors:** §8 (LabellerError transient row), §6.3
- **Options considered:**
  1. Retry on every non-2xx, every httpx exception. Maximally permissive. Wastes attempts on 400/422 (malformed request) which are never going to succeed.
  2. Retry only on the spec's literal mention: 429, 500, 502, 503, 504, `httpx.TimeoutException`, `httpx.ConnectError`. Non-retryable: 4xx (excluding 429), `RemoteProtocolError`, `ReadError`, `WriteError`.
  3. Same as 2 plus `RemoteProtocolError` (server crashed mid-response — likely transient if the server restarts cleanly).
- **Chosen:** Option 3.
- **Reasoning:** The spec is illustrative on the 5xx set; the chosen list — {429, 500, 502, 503, 504} — is the canonical retryable HTTP-status family. Adding `RemoteProtocolError` to the retry set covers the realistic "VM server got OOM-killed mid-response" case. 4xx (non-429) stays non-retryable: a 400 or 422 means the request was wrong; retrying without changing it is pointless. The backoff schedule is the spec's literal "1 s → 2 s" extended to 4 s via `2**attempt` for the (rare) case where `retries=3` is configured.
- **Out-of-scope alternatives deferred:** Jitter on the backoff; `Retry-After` header parsing; circuit-breaker on consecutive failures.
- **Affected files:** `src/labelling/remote_labeller.py`
- **Commit:** pending
- **Supersedes:** —

### D-012: `image_path` translation — must be under `local_image_root`

- **Timestamp:** 2026-05-16 13:10 (local)
- **Task:** Task 3 — Remote labeller + runner
- **Trigger:** Spec §5.1 says the request carries an absolute VM path. The local harness has the file at a local path. The translation rule (how to derive the VM path from the local path + config) needs to be pinned.
- **Spec anchors:** §5.1 (`image_path` request field), §6.5 (`remote_image_root`, `local_image_root` config fields), §13 ("Image-root path on the VM" gap)
- **Options considered:**
  1. The user supplies the VM path directly via CLI for every image. Operator-hostile at 500 images.
  2. String-replace `local_image_root` prefix with `remote_image_root` on every image_path. Fragile to symlinks, relative paths, trailing slashes.
  3. `image_path.resolve().relative_to(Path(local_image_root).resolve())` → join with `remote_image_root`. Robust to relative paths and symlinks; raises `ValueError` if the image is not under the configured root, which becomes a `LabellerError` with a clear message.
- **Chosen:** Option 3 (`relative_to` after resolve).
- **Reasoning:** This handles the realistic cases — `Beispiele/duct/<x>.jpeg` resolved from a CWD-relative path, `Fotos/<x>.jpeg` similarly, and ad-hoc absolute paths — uniformly. Failure mode is explicit: if the operator points at an image outside `local_image_root` (e.g. forgets to update the root after moving Beispiele/), the error fires immediately on the first image rather than after a confusing 404 from the server. Matches the spec's §13.last gap on server-side path-validation: same invariant from the other end.
- **Out-of-scope alternatives deferred:** Multi-root support (different roots for `Fotos/` vs `Beispiele/`). Single root is enough at hackathon scale; if needed, the operator rsyncs both into `<remote_image_root>/Fotos` and `<remote_image_root>/Beispiele` and the relative-path rule continues to work.
- **Affected files:** `src/labelling/remote_labeller.py`
- **Commit:** pending
- **Supersedes:** —

### D-013: Signal handling + always-write-manifest invariant

- **Timestamp:** 2026-05-16 13:15 (local)
- **Task:** Task 3 — Remote labeller + runner
- **Trigger:** Spec §7 says "the runner registers a SIGINT/SIGTERM handler that drains state to disk before exiting" and "a run that started always produces `run_manifest.json` with a final state, even if every image failed". Implementation needs to guarantee the manifest write happens on Ctrl-C and on any uncaught exception.
- **Spec anchors:** §7 (class invariant), §8
- **Options considered:**
  1. `try/finally` around the loop only, with no signal handler. Ctrl-C raises KeyboardInterrupt which the finally catches — works on POSIX, awkward to test, doesn't catch SIGTERM cleanly.
  2. `atexit.register` to write the manifest. Doesn't run on SIGTERM (default disposition is to terminate without atexit).
  3. Install SIGINT + SIGTERM handlers that set a flag; the per-image loop checks the flag at iteration start and raises a sentinel `_Interrupted` exception; outer `try/finally` writes the manifest. Restore prior handlers on exit so test/CLI callers don't get persistent handlers.
- **Chosen:** Option 3 (signal flag + finally + handler restore).
- **Reasoning:** Sentinel-exception pattern is the standard way to interrupt an in-flight loop without losing the manifest write. Restoring prior handlers means a pytest run that calls `runner.run()` cannot accidentally leave the test's handler chain modified. The flag-based approach also gives a deterministic test path: the test can install the flag manually instead of sending a real signal.
- **Out-of-scope alternatives deferred:** Per-image timeout enforcement at the runner level (httpx handles per-request timeout via config.timeout_seconds; the runner just trusts the labeller's per-image latency).
- **Affected files:** `src/labelling/runner.py`
- **Commit:** pending
- **Supersedes:** —

### D-014: Class IDs derived from `config.classes` position, not a separate mapping

- **Timestamp:** 2026-05-16 13:20 (local)
- **Task:** Task 3 — Remote labeller + runner
- **Trigger:** YOLO `<stem>.txt` lines need integer class IDs. The harness deals in class names throughout (`Detection.cls`, `config.classes`). Need a source of truth for `name → id`.
- **Spec anchors:** §6.2 (YOLO line format), §6.5 (`classes: list[str]`)
- **Options considered:**
  1. A separate `data.yaml` lookup at write-time. Crosses module boundaries (runner depends on the dataset config) and adds yet another moving piece.
  2. The position of the class name in `config.classes` IS the id. The runner does `config.classes.index(det.cls)`. The convention of "the YAML order is the wire order" is the simplest contract.
  3. An explicit `class_to_id: dict[str, int]` field on `LabellerConfig`. Lets the operator pin IDs explicitly; redundant with `classes:` ordering unless someone wants to reorder without renumbering.
- **Chosen:** Option 2 (position is id).
- **Reasoning:** `config.classes` already orders the classes; the YOLO writer uses that order. Operators get the canonical ID assignment by matching `data.yaml`'s `names:` order in the harness config — that's their responsibility and it surfaces immediately on the first run (a mismatch would change which int appears in `.txt`). One source of truth, no drift opportunity.
- **Out-of-scope alternatives deferred:** Validating at runtime that `config.classes` matches `data.yaml`'s `names:` mapping. Could be a CLI flag in T6 if needed.
- **Affected files:** `src/labelling/runner.py`
- **Commit:** pending
- **Supersedes:** —

---

### D-015: Compare CLI accepts either a `labels/` dir or its parent

- **Timestamp:** 2026-05-16 14:00 (local)
- **Task:** Task 5 — Compare tool
- **Trigger:** Spec §5.6 CLI example shows `labelling/labels/` and `labelling/runs/grounding-dino_<ts>/labels/` — both literal `labels/` dirs. The v2 baseline is at `labelling/labels/`; the v3 outputs are at `labelling/runs/<profile>_<ts>/labels/`. Operators are likely to pass the run dir (parent of `labels/`) by mistake.
- **Spec anchors:** §5.6 (CLI surface), §6.6 (compare output)
- **Options considered:**
  1. Strict — only accept the literal `labels/` dir; error out on the parent. Matches the spec example exactly but is brittle.
  2. Auto-resolve — if the passed path has a `labels/` subdirectory, descend into it; otherwise treat the path as a labels dir directly. The spec example's behaviour is preserved, the friendlier case (passing the run dir) just works.
  3. Add a `--labels-subdir` flag. Bloats the CLI.
- **Chosen:** Option 2 (auto-resolve).
- **Reasoning:** Strictly compatible with the spec example (passing `labels/` directly still works), but tolerates the parent dir which is the natural thing to copy-paste from the runner's stdout (`run_dir: labelling/runs/grounding-dino_<ts>/`). One less footgun at hackathon pace, no API surface added.
- **Out-of-scope alternatives deferred:** Reading `run_manifest.json` to discover the labels dir — overengineered; the dir-name convention is enough.
- **Affected files:** `src/labelling/compare.py`, `scripts/compare_runs.py`
- **Commit:** pending
- **Supersedes:** —

### D-016: IoU > 0 threshold for a "match" in greedy pairing

- **Timestamp:** 2026-05-16 14:05 (local)
- **Task:** Task 5 — Compare tool
- **Trigger:** Greedy matching needs a floor on what counts as a match. A pair with IoU = 0 (no overlap) should not consume a b-box; otherwise an a-box could "match" a far-away b-box just to claim it, hiding a genuine miss.
- **Spec anchors:** §6.6, §13 ("greedy IoU matching" gap)
- **Options considered:**
  1. Any IoU ≥ 0 counts — even no-overlap pairs greedily claim a b-box. Worst: an a-box always finds a "match" even when nothing nearby exists, so missing detections look matched-with-low-IoU rather than unmatched.
  2. IoU > 0 (strictly positive overlap) — unmatched a-boxes record -1 honestly. Cheap.
  3. IoU > 0.5 (canonical detection threshold) — a low-but-real overlap counts as no-match. Strict; could under-count real-but-loose matches between v2 (VLM-loose) and v3 (model-tighter).
- **Chosen:** Option 2 (IoU > 0).
- **Reasoning:** The diff tool is for operator review, not for AP/recall computation. Strictly-positive overlap means -1 is reserved for "the other run did not detect this region at all" — the actionable signal. Loose matches (IoU = 0.2) are still visible in the per-photo numbers; the operator can decide whether to call them matches at the threshold of their choice. A canonical 0.5 cutoff would discard the visibility of "yes there's a box in roughly the right place but it's loose" cases — those are the most useful ones to inspect.
- **Out-of-scope alternatives deferred:** A configurable `--min-iou` flag; can be added later if the operator wants stricter pairing.
- **Affected files:** `src/labelling/compare.py`
- **Commit:** pending
- **Supersedes:** —

### D-017: `per_class_mean_iou_when_both_present` excludes unmatched (-1.0) IoUs from the mean

- **Timestamp:** 2026-05-16 14:08 (local)
- **Task:** Task 5 — Compare tool
- **Trigger:** Summary stat needs a definition. With unmatched a-boxes scoring -1.0, naive averaging would skew the mean negative. Need to decide whether -1.0 affects the per-class mean.
- **Spec anchors:** §6.6 (summary block)
- **Options considered:**
  1. Average over ALL ious (including -1) — produces a number that mixes "boxes that matched" with "boxes that didn't", uninterpretable.
  2. Average over only positive ious — produces "when both runs find a box in this class on the same photo, how tight is the IoU between them?" — interpretable.
  3. Use F-style: harmonic of pairwise IoU and presence-recall. Overengineered for a summary line.
- **Chosen:** Option 2.
- **Reasoning:** The summary key explicitly says "when both present", which is itself a presence filter — extending that to "when the boxes can actually be paired" is the natural reading. Operators who want presence-recall can compute it from `class_presence_agreement_rate` and the per-class iou independently. Mixed scoring would dilute the signal — a class where v3 missed half the v2 boxes would average to ~IoU 0.3 even if every matched pair was perfect.
- **Out-of-scope alternatives deferred:** Reporting median/p95 of IoUs as well as mean — single-stat summary is enough at hackathon scale.
- **Affected files:** `src/labelling/compare.py`
- **Commit:** pending
- **Supersedes:** —

---

### D-018: Manifest path resolution — CLI flag with dataset-rooted default

- **Timestamp:** 2026-05-16 14:30 (local)
- **Task:** Task 6 — CLI entry point
- **Trigger:** Spec §5.6 / §6.5 are silent on where `manifest.csv` lives. The CLI needs to load it; the path can be (a) hardcoded, (b) a field on `LabellerConfig`, (c) a CLI flag.
- **Spec anchors:** §5.6 (CLI flags), §6.5 (config schema — does NOT include manifest_csv)
- **Options considered:**
  1. Add `manifest_csv` to `LabellerConfig`. Couples the profile to the dataset. The same Grounding DINO profile would need a different config to label a different dataset.
  2. Hardcode the path. Fastest but invisible.
  3. Add `--manifest` CLI flag defaulting to `<repo>/project-resources/custom-datasets/duct-and-ruler/detection/labelling/manifest.csv`. The dataset is a CLI concern; the model profile is content-agnostic.
- **Chosen:** Option 3 (CLI flag with default).
- **Reasoning:** Manifest is a dataset property and the profile YAML should stay portable (same profile, different dataset). Putting it on the CLI keeps that separation and gives operators an obvious knob if they ever label a different sampled set. Default makes the common case zero-touch. Same reasoning applies to `--out` (dataset-rooted default).
- **Out-of-scope alternatives deferred:** Auto-discovering the manifest from `data.yaml`'s `path:` field — coupling the harness to Ultralytics-shaped configs is more than this hackathon needs.
- **Affected files:** `scripts/label.py`
- **Commit:** pending
- **Supersedes:** —

### D-019: `_resolve_image` accepts both `local_image_root=project-resources` and `local_image_root=project-resources/Fotos`

- **Timestamp:** 2026-05-16 14:35 (local)
- **Task:** Task 6 — CLI entry point
- **Trigger:** The manifest's `filename` column has bare names (e.g. `WhatsApp Image 2024-11-21 at 20_25_53.jpeg`); the files actually live under `project-resources/Fotos/`. The config's `local_image_root` could either point at `project-resources/` (parent, expecting `Fotos/` subdir) or at `project-resources/Fotos/` directly. Either is a reasonable operator interpretation.
- **Spec anchors:** §6.5 (`local_image_root`), §13 ("Image-root path on the VM" gap — local mirror needed too)
- **Options considered:**
  1. Strict — operator must set `local_image_root=project-resources/Fotos`. The remote and local roots then mismatch in structure (remote has `Fotos/<filename>`, local has `<filename>`) — confusing.
  2. Strict — operator must set `local_image_root=project-resources` (parent), and the resolver always prepends `Fotos/`. Mirrors the remote layout but hardcodes the `Fotos/` segment.
  3. Try both — `Fotos/<filename>` first, then `<filename>`. The resolver does the right thing under both operator interpretations; the missing-image error is deferred to `label()` which fails with a clear message.
- **Chosen:** Option 3.
- **Reasoning:** Hackathon-friendly: zero operator surprise either way. The `_to_remote_path` translation logic on the labeller side uses `local_image_root` as a prefix-to-strip, so as long as the chosen path is under that root, the remote path computes correctly. The two-candidate resolver maps to the same remote URL in both setups because the remote upload mirrors the local subtree (Fotos under remote_image_root either way).
- **Out-of-scope alternatives deferred:** Reading filenames from `manifest.csv` that already contain a `Fotos/` prefix — manifest format is fixed (§14 non-goal "don't change manifest.csv structure").
- **Affected files:** `scripts/label.py`
- **Commit:** pending
- **Supersedes:** —

---

### D-020: Test fixtures created inline; no checked-in image binaries

- **Timestamp:** 2026-05-16 15:00 (local)
- **Task:** Task 7 — Local tests
- **Trigger:** Spec §13 "Test fixtures" gap mentions using "2–3 small JPEGs from `Beispiele/duct/`" with a < 50 KB cap. In practice the labeller code path never decodes the image — it only passes the path to the server. The runner writes only the `.txt` / `.json` outputs based on `LabelOutput` (which is fully synthesisable). No need for real image bytes anywhere in the unit + mocked-integration tests.
- **Spec anchors:** §10 (testing strategy), §13 ("Test fixtures" gap)
- **Options considered:**
  1. Check in 2–3 small JPEGs from `Beispiele/duct/` and reference them in tests. Requires the dataset to be present (it's gitignored in `project-resources/`), so CI without the dataset would fail.
  2. Tests synthesise file path stubs via `tmp_path.write_bytes(b"...")` — file exists with a fake JPEG header, never decoded, never read. Tests can run on any checkout.
  3. Add a `tests/data/` directory of tiny synthetic JPEGs created at conftest time. More machinery; no benefit over option 2.
- **Chosen:** Option 2 (in-test synthesis via `tmp_path`).
- **Reasoning:** None of the unit/mocked-integration tests need real image bytes — the harness's image-aware code lives on the VM. Synthetic paths keep tests self-contained, fast, and CI-portable. If a smoke test that actually opens a JPEG is ever added, it can fall back to a real Beispiele file at that time.
- **Out-of-scope alternatives deferred:** A real end-to-end smoke test that hits a live local FastAPI process; that's an operator gate, not a unit test.
- **Affected files:** `tests/labelling/test_resume.py`, `tests/labelling/test_remote_integration.py`
- **Commit:** pending
- **Supersedes:** —

### D-021: Backoff function monkeypatched in tests to skip real sleeps

- **Timestamp:** 2026-05-16 15:05 (local)
- **Task:** Task 7 — Local tests
- **Trigger:** The retry path uses `time.sleep(_backoff_seconds(attempt))` for 1 s and 2 s delays. Running unit tests against that path would add ≥3 s wall-clock per retry test and make `pytest -q` painful at hackathon iteration speed.
- **Spec anchors:** §8 (retry policy with 1 s / 2 s backoff), §10 (testing strategy)
- **Options considered:**
  1. Use `time.monotonic` mocks or `unittest.mock.patch("time.sleep")`. Mocks the entire `time` module surface; brittle.
  2. Extract `_backoff_seconds` as a module-level function and `monkeypatch` it to `lambda _: 0.0` in retry tests. The function is the single seam between policy and sleeping; monkeypatching it skips the wait without disabling sleep globally.
  3. Configure `retries: 0` in test configs. Bypasses the retry path entirely — can't verify the retry behaviour at all.
- **Chosen:** Option 2 (monkeypatch the named seam).
- **Reasoning:** Keeps the production retry timings exact (no test-only branching in `label()`) while giving deterministic, instant tests. The seam is small and named, so the test's intent reads cleanly: "retry, but with zero delay so the test stays under a millisecond". The actual retry behaviour (count, conditions, exception types) is still exercised at full fidelity.
- **Out-of-scope alternatives deferred:** Test-double clock / `freezegun` — overkill for one function.
- **Affected files:** `src/labelling/remote_labeller.py` (extracted `_backoff_seconds`), `tests/labelling/test_remote_integration.py`
- **Commit:** pending
- **Supersedes:** —

---

### D-022: VM scaffold mirrored at `vm-server/` in the local repo

- **Timestamp:** 2026-05-16 16:00 (local)
- **Task:** Task 8 — VM scaffold + Grounding DINO adapter
- **Trigger:** Spec §11 lists `~/repos/vision/` files under "VM" only. The local repo has no link to them, making post-hoc audit of what got deployed difficult and leaving the VM code without version control.
- **Spec anchors:** §4.4, §4.5, §11 ("VM (~/repos/vision/)" section)
- **Options considered:**
  1. Files live on the VM only (literal spec interpretation). No local audit trail; the VM is a black box for the auditor.
  2. Mirror the VM files at `vm-server/` in the local repo. Deploy via `tar -C vm-server -cf - . | ssh threenicorn 'cd ~/repos/vision && tar xf -'`. Local repo is source-of-truth; the VM is a deployment target. Adds a small directory to the local repo's diff.
  3. Make the VM its own separate git repo with its own history. Cleanest separation; biggest operational overhead for a hackathon (two repos to keep in sync, two PR cycles, etc.).
- **Chosen:** Option 2 (mirror at `vm-server/`).
- **Reasoning:** The local repo already contains the spec, ledger, harness, configs, and tests. Mirroring the VM code keeps the entire feature reviewable in one diff and gives the auditor concrete files to inspect against §4.4 / §4.5. Deployment is one tar-over-ssh away. The audit-visibility benefit outweighs the small diff cost.
- **Out-of-scope alternatives deferred:** Setting up a separate git repo on the VM and a CI deployment pipeline — overkill at hackathon scale.
- **Affected files:** `vm-server/*` (all of it), plus a brief mention in the runbook (T9).
- **Commit:** pending
- **Supersedes:** —

### D-023: Grounding DINO adapter — fp32 weights + bf16 autocast (not bf16 weights)

- **Timestamp:** 2026-05-16 16:15 (local)
- **Task:** Task 8 — VM scaffold + Grounding DINO adapter
- **Trigger:** Loading the model with `torch_dtype=torch.bfloat16` failed at inference with cascading dtype mismatches — first in the Swin patch-embed conv (`Float vs BFloat16` on `pixel_values`), then in the text-enhancer cross-attention (`mat1 and mat2 must have the same dtype` on the BERT query projection). The processor emits fp32 tensors for both image and text; manually casting one path leaves the other broken.
- **Spec anchors:** §4.5 (adapter responsibility), §8 (OOM row)
- **Options considered:**
  1. Hunt down every fp32 → bf16 cast site in the processor output (`pixel_values`, `input_ids`, `attention_mask`, `pixel_mask`, `token_type_ids`, etc.) and cast each before forward. Brittle, breaks on minor Transformers version bumps that add/rename fields.
  2. Load the model in fp32 and run forward under `torch.autocast(device_type="cuda", dtype=torch.bfloat16)`. PyTorch's autocast handles the up/down-casts at each op-call site as needed; speed is comparable to manual bf16 in practice; no manual cast plumbing.
  3. Keep the model in fp32 with no autocast. Slowest (about 2× the bf16 throughput on a 5090) but simplest. ~80–120 ms/image vs ~40–60 ms — still well under the spec's hackathon-scale target.
- **Chosen:** Option 2 (fp32 weights + autocast).
- **Reasoning:** Option 1 lost two debug cycles already during T8; the dtype surface is too wide. Option 2 is the canonical PyTorch recommendation for inference at lower precision when the model isn't natively trained at that precision. Autocast keeps the forward pass mixed-precision (matmuls and convs in bf16, layer-norms and softmaxes in fp32) which matches the trained-precision the weights expect. Verified by a successful end-to-end /detect call on a Beispiele/duct image returning 3 detections in 801 ms (first call, includes JIT compile).
- **Out-of-scope alternatives deferred:** ONNX export with bf16 quantisation — out of scope; the harness uses HF inference directly.
- **Affected files:** `vm-server/server/adapters/grounding_dino.py`
- **Commit:** pending
- **Supersedes:** —

### D-024: `post_process_grounded_object_detection(threshold=)`, not `box_threshold=`

- **Timestamp:** 2026-05-16 16:25 (local)
- **Task:** Task 8 — VM scaffold + Grounding DINO adapter
- **Trigger:** First call to `post_process_grounded_object_detection(box_threshold=…)` failed with `TypeError: ... got an unexpected keyword argument 'box_threshold'`. The Transformers API renamed it to `threshold` somewhere between 4.45 and 4.57.
- **Spec anchors:** §4.5 (adapter)
- **Options considered:**
  1. Pin Transformers to a pre-rename version (e.g. 4.45) that accepts `box_threshold`. Locks the deployment to a stale version.
  2. Use the current name (`threshold=`). Tracks upstream; subject to future renames.
  3. Try-import a probe at adapter load and pick the parameter name at runtime. Defensive but over-engineered for one keyword.
- **Chosen:** Option 2 (use `threshold=`).
- **Reasoning:** The deployed Transformers (4.57.6 via uv sync) settled on `threshold=`. Pinning to 4.45 would block bug fixes and new model adapters; a runtime probe doesn't earn its keep for a one-line keyword. The breakage from a future rename would be loud (TypeError at first /detect call) and easy to fix — log it in the ledger when it happens.
- **Out-of-scope alternatives deferred:** Wrapping the post-processor in a compatibility shim.
- **Affected files:** `vm-server/server/adapters/grounding_dino.py`
- **Commit:** pending
- **Supersedes:** —

### D-025: Single-pass concatenated prompt + substring-match for label→class

- **Timestamp:** 2026-05-16 16:30 (local)
- **Task:** Task 8 — VM scaffold + Grounding DINO adapter
- **Trigger:** Grounding DINO accepts multi-class queries via a single text prompt with class boundaries marked by `.`. Detections come back tagged with the matched text span — not with the operator-facing class name. Need a mapping from span → class.
- **Spec anchors:** §4.5, §5.1, §5.2
- **Options considered:**
  1. Per-class forward pass — run inference 4× per image, once per class, with that class's prompt only. Simplest mapping (output is naturally tagged), but 4× the inference cost (~200 ms per image instead of ~50 ms).
  2. Single-pass concatenated prompt; map each detected span back to a class by substring-matching the span text against each class's prompt. Cheap, one forward pass; mapping is heuristic — a span could in principle match multiple classes' prompts if their wording overlaps (e.g. `paper` appears in both `whitepaper` and `sitetag`).
  3. Single-pass with per-class boundary-token tracking via char offsets through the concatenated prompt. More precise mapping; requires reproducing the tokenizer's offset behaviour. Complex.
- **Chosen:** Option 2 (single-pass + substring match).
- **Reasoning:** 4× speedup matters for a 500-image labelling run (50 ms × 500 = 25 s vs 200 ms × 500 = 100 s). Substring ambiguity is bounded by prompt authoring — the harness operator should keep per-class prompts non-overlapping. Falls back to a token-level match if the full label isn't found in any prompt, so partial matches still resolve. Edge cases (a label that overlaps two prompts) get assigned to the first matching class, which makes the failure mode predictable.
- **Out-of-scope alternatives deferred:** Option 3's offset-tracking — revisit if substring matching produces frequent miscategorisations on real data.
- **Affected files:** `vm-server/server/adapters/grounding_dino.py`
- **Commit:** pending
- **Supersedes:** —
