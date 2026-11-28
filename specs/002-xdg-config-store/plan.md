# Implementation Plan: XDG Configuration and Neutral Store Default

**Branch**: `002-xdg-config-store` | **Date**: 2026-11-27 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-xdg-config-store/spec.md`

## Summary

Move all path resolution (config folder, data folder, store, personal profiles folder) into one new stdlib-only module, `cfplib/paths.py`, and make both the CLI (`cfp_store.py` via `cfplib/config.py`) and the session context hook import it, so they can never disagree (FR-004). The store falls back to `<data folder>/store` instead of failing. Seed handling in `cfplib/seeds.py` gains a second source (`<data folder>/profiles`) that overrides shipped profiles of the same name, with a `warnings` list and a `source` label per seed. `/cfp:init` proposes the resolved default instead of an Obsidian vault, the shared preamble learns a `<store-error>` element, and the README, guide, and feature 001 artifacts are updated.

## Technical Context

**Language/Version**: Python 3 (stdlib only at runtime, invoked as `python3 -I`), same as feature 001

**Primary Dependencies**: none at runtime; pytest in `~/.venvs/cc-cfp` for tests

**Storage**: markdown files with YAML front matter in the store; `config.json` in the config folder

**Testing**: pytest (`make test`), `make test-hook`, `make lint-dashes`

**Target Platform**: macOS and Linux, Claude Code plugin

**Project Type**: Claude Code plugin (skills + CLI scripts + hook)

**Performance Goals**: the hook stays well under its 5 s timeout (a few `stat` calls added)

**Constraints**: no venv at runtime; `python3 -I` means the hook cannot rely on `PYTHONPATH` and must add `scripts/` to `sys.path` itself; no em-dash or en-dash characters; hook never exits non-zero for a `/cfp:` prompt

**Scale/Scope**: about 6 source files, 3 skill/doc files, 4 guide/README files, 4 feature 001 artifacts

## Constitution Check

The project constitution (`.specify/memory/constitution.md`) is still the unfilled template, so there are no ratified gates. The feature 001 conventions act as the de facto rules and are kept: stdlib-only scripts, JSON-out CLI with `ok`, store files stay hand-editable, skills never edit store files directly, no dashes in prose. No violations.

## Project Structure

### Documentation (this feature)

```text
specs/002-xdg-config-store/
├── spec.md
├── plan.md              # this file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   ├── paths.md         # resolution rules and errors
│   ├── cli.md           # changed CLI outputs (config show, config init, seed-status, seed-update)
│   └── hook.md          # <cfp-context> with <store-error>
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
cfp/
├── hooks/scripts/context-hook.py     # imports cfplib.paths; emits <store-error>
├── scripts/
│   ├── cfp_store.py                  # config show/init outputs, seed commands pass user dir
│   ├── cfplib/
│   │   ├── paths.py                  # NEW: config dir, data dir, store, user profiles dir
│   │   ├── config.py                 # uses paths; legacy fallback; write location
│   │   └── seeds.py                  # two seed sources, override, warnings, source label
│   └── test/
│       ├── conftest.py               # isolate XDG_* and CFP_* env vars
│       ├── test_paths.py             # NEW: resolution matrix (SC-003)
│       ├── test_hook.py              # NEW: hook agrees with CLI
│       ├── test_config.py            # extended
│       └── test_seeds.py             # extended: user seeds, clash, newer/outdated
├── skills/
│   ├── _shared/preamble.md           # <store-error>, <store> description
│   └── init/SKILL.md                 # neutral default, vault cap, warnings, report
README.md
docs/guide/content/modules/ROOT/pages/overview/install.adoc
docs/guide/content/modules/ROOT/pages/reference/commands.adoc
specs/001-cfp-plugin/{spec.md,plan.md,research.md,contracts/commands.md,contracts/store-files.md}
```

**Structure Decision**: single plugin tree as in feature 001. The only new source module is `cfplib/paths.py`; it has no imports from other `cfplib` modules except `CfpError`, so the hook can import it cheaply.

## Design Notes

1. **One resolver** (`cfplib/paths.py`): pure functions taking an optional `env` mapping and `home` path (default `os.environ`, `Path.home()`), so tests drive the full matrix without monkeypatching globals. See [contracts/paths.md](contracts/paths.md).
2. **Store source**: `resolve_store(cli_store)` returns `(path, source)` where source is `argument | environment | config | default`. `config.resolve_store` keeps its current return type (a `Path`) for existing callers; `config show` uses the new tuple form.
3. **Legacy fallback**: only when `CFP_CONFIG_DIR` is unset and the resolved `config.json` does not exist. `load_user_config()` keeps returning a plain `dict`; `config show` calls `paths.read_config()` to learn the path that was read.
3a. **Invalid `CFP_DATA_DIR`**: `config show`, `config init`, `profile seed-status`, and `profile seed-update` fail with the `CfpError` (FR-002); other commands only fail when store resolution falls through to the default store.
4. **Hook**: inserts `<plugin-root>/scripts` into `sys.path`, imports `cfplib.paths`. Any `CfpError` (or any unexpected exception) becomes `<store-error>` with an empty `<store>`. Hook still exits 0.
5. **Seeds**: `seeds.collect(plugin_dir, user_dir=None) -> (entries, warnings)` with entries `{name, dir, source}`. User entries replace plugin entries of the same name. Library signatures: `seeds.status(store_path, seed_dir, user_dir=None) -> list` (unchanged shape, entries gain `source`/`seed_dir`), `seeds.status_report(store_path, seed_dir, user_dir=None) -> (list, warnings)`, `seeds.update(store_path, seed_dir, profile_id, files=None, all_files=False, user_dir=None) -> dict` (adds `source`, `warnings`), `config.init_store(store, values, seed_dir=None, user_seed_dir=None)` (result adds `warnings`). In the library `user_dir=None` means no user source; the CLI passes `paths.user_profiles_dir()` or the hidden `--user-seed-dir` test override. Diffs for user seeds label the target `user/<rel>`.
6. **Newer/outdated wording for user seeds**: the state values stay as in feature 001; each status entry gains `source` and `seed_dir`. The init skill picks the wording by `source`. A user variant without `seed_version` on top of a store copy that has one yields state `current` today; the clash warning text says the variant will not replace the store copy (spec edge case).
7. **`CFP_STORE` warning at init**: `config init` returns `warnings` with an entry when `CFP_STORE` is set and differs from the chosen store.
8. **Init skill**: default from `config show` (`store` + `store_source`), vault choices capped at 3, collects `warnings` from `config init` and `seed-status`, de-duplicates by profile before showing, report names `user_profiles_dir`.

## Complexity Tracking

No constitution violations to justify.
