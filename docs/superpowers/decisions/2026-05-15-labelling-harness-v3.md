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
