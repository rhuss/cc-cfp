# Tasks: XDG Configuration and Neutral Store Default

**Input**: Design documents from `specs/002-xdg-config-store/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Included. The project tests every script behavior with pytest (feature 001 convention), and SC-003 requires a resolution matrix test. Write each test before its implementation and see it fail first.

**Test command**: `make test` (pytest in `~/.venvs/cc-cfp`), plus `make test-hook` and `make lint-dashes`.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

- [X] T001 Isolate tests from the real environment in `cfp/scripts/test/conftest.py`: the `tmp_home` fixture `monkeypatch.delenv(..., raising=False)` for `XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `CFP_CONFIG_DIR`, `CFP_DATA_DIR`, `CFP_STORE` (and keeps setting `HOME`); `tmp_store` sets `CFP_STORE` again afterwards as today; `run_cli(..., env=...)` accepts `None` values that remove a variable from the subprocess env (for example `env={"CFP_STORE": None}`). Run `make test` and confirm the existing suite still passes.

## Phase 2: Foundational (blocks all stories)

- [X] T002 Write `cfp/scripts/test/test_paths.py` covering `contracts/paths.md`, passing `env` and `home` explicitly: config dir order (`CFP_CONFIG_DIR` > `$XDG_CONFIG_HOME/cc-cfp` > `~/.config/cc-cfp`); data dir order (`CFP_DATA_DIR` > `$XDG_DATA_HOME/cc-cfp` > `~/.local/share/cc-cfp`); XDG values ignored "when empty or not absolute"; empty or whitespace-only `CFP_*` values count as unset (empty `CFP_CONFIG_DIR` keeps the legacy fallback); `~` expansion then rejection of relative `CFP_CONFIG_DIR`/`CFP_DATA_DIR`/`CFP_STORE` with message `<VAR> must be an absolute path, got '<value>'`; `read_config` legacy fallback only "when `CFP_CONFIG_DIR` unset and the resolved file does not exist"; malformed or non-object resolved file gives `({}, path)` without fallback; config `store` value: `~` expanded, relative resolved against the config folder, non-string ignored; `resolve_store` order and `source` values `argument|environment|config|default`; lazy evaluation (`--store` ignores broken `CFP_STORE`/`CFP_CONFIG_DIR`/`CFP_DATA_DIR`; valid `CFP_STORE` ignores broken `CFP_CONFIG_DIR`/`CFP_DATA_DIR`). Tests must fail (module missing).
- [X] T003 Implement `cfp/scripts/cfplib/paths.py` per `contracts/paths.md` (stdlib only, imports only `CfpError` from `cfplib`, never creates folders). Make T002 pass.
- [X] T004 Refactor `cfp/scripts/cfplib/config.py` to use `paths`. Interfaces: `user_config_path() -> Path` returns `paths.config_file()`; `load_user_config() -> dict` (unchanged return type) uses `paths.read_config()[0]`; `write_user_config(store) -> Path` writes `paths.config_file()` (creating its parent), preserving unknown keys from the file that was read; `resolve_store(cli_store) -> Path` (unchanged) delegates to `paths.resolve_store()`; new `resolve_store_with_source(cli_store) -> (Path, str)`. Update the module docstring. In `cfp/scripts/test/test_config.py`: replace expectations of the "no store configured" error with the new default `<home>/.local/share/cc-cfp/store`; add a test that writes go to `$XDG_CONFIG_HOME/cc-cfp/config.json` and the legacy file is left untouched. In `cfp/scripts/test/test_cli_foundation.py`: rename `test_no_store_configured_at_all` and change it to assert the default store and the "store not initialized" error for commands other than `config show`/`config init`.

**Checkpoint**: `make test` green; resolution lives in one module.

## Phase 3: User Story 1, Neutral store default at first setup (P1)

**Goal**: init proposes `<data folder>/store` as an absolute path; Obsidian vaults are extra choices only.
**Independent test**: scratch HOME without `~/Obsidian`: `config show` reports the XDG store with `store_source: default`; `/cfp:init` proposes it.

- [X] T005 [US1] Add CLI tests in `cfp/scripts/test/test_cli_foundation.py` (use `env={"CFP_STORE": None}` where nothing may be configured): `config show` returns `store`, `store_source`, `exists`, `config`, `config_file`, `config_write_path`, `data_dir`, `user_profiles_dir` per `contracts/cli.md`; with nothing configured `store` equals `<home>/.local/share/cc-cfp/store` and `config_file` is `null`; `config show` and `config init` fail with `CFP_DATA_DIR must be an absolute path` for `CFP_DATA_DIR=rel`; `config init` without `--store` and without `CFP_STORE` creates that folder including parents, returns `config_write_path` and `user_profiles_dir`, writes `config.json` naming the store, and does NOT create `<data dir>/profiles`; `config init` overwrites a malformed `config.json` with a valid one; `config init --store X` with `CFP_STORE=Y` returns a `warnings` entry `CFP_STORE is set to 'Y' and overrides the saved store 'X' in later sessions`, and no warning when `CFP_STORE` is `~/x` and the store is the expanded `<home>/x`.
- [X] T006 [US1] Implement in `cfp/scripts/cfp_store.py`: `cmd_config_show` adds `store_source`, `config_file`, `config_write_path`, `data_dir`, `user_profiles_dir` (an invalid `CFP_DATA_DIR` raises, per contracts/cli.md); `cmd_config_init` resolves the store through `config.resolve_store`, adds `warnings` (CFP_STORE override, comparing expanded resolved paths), `config_write_path`, `user_profiles_dir`. Make T005 pass.
- [X] T007 [US1] Update `cfp/skills/init/SKILL.md`: Step 1 gets the default from `config show` (`store`, absolute) instead of globbing Obsidian, offers it first as recommended, Globs `~/Obsidian/*` and adds up to three `~/Obsidian/<vault>/Talks` choices "sorted by name", free text for anything else; Step 5 says the command writes the config file named in `config_write_path` (not a fixed `~/.config/cc-cfp/config.json`) and shows `warnings`; Step 7 report adds the config file and `user_profiles_dir` ("put personal conference profiles here"); replace "can be edited in Obsidian" with "can be edited in any editor or opened as an Obsidian vault".

**Checkpoint**: Story 1 works with scripts and skill.

## Phase 4: User Story 2, Config follows XDG and can be relocated (P1)

**Goal**: scripts and the session hook resolve the same config folder and store; errors surface as `<store-error>`.
**Independent test**: `CFP_CONFIG_DIR=/tmp/x` init writes there; hook `<store>` equals `config show` `store`.

- [X] T008 [P] [US2] Write `cfp/scripts/test/test_hook.py`: run `python3 -I cfp/hooks/scripts/context-hook.py` with stdin `{"prompt":"/cfp:status"}` and a controlled env; parametrize the SC-003 matrix (`CFP_STORE` set/unset x config location `CFP_CONFIG_DIR`/`XDG_CONFIG_HOME`/home/legacy x store entry present/absent, each with `CFP_DATA_DIR` unset and set) and assert `<store>` equals the CLI `config show` `store`; over the same matrix assert `config show --store X` returns X (also with `CFP_DATA_DIR=rel`, where `config show` itself must fail, so use `profile list --store X` for that case); assert a relative `CFP_STORE` yields empty `<store>`, `<store-initialized>false</store-initialized>`, and `<store-error>CFP_STORE must be an absolute path, got 'talks'</store-error>`, exit code 0; a store path containing `&` is XML-escaped; a non-`/cfp:` prompt yields no output.
- [X] T009 [US2] Rewrite `resolve_store` in `cfp/hooks/scripts/context-hook.py`: insert `<plugin_root>/scripts` into `sys.path`, import `cfplib.paths`, call `paths.resolve_store(None)`; on any exception emit empty `<store>`, `false`, and `<store-error>` with the message; XML-escape both the store value and the error text; keep exit 0 and the module docstring accurate. Make T008 pass and run `make test-hook`.
- [X] T010 [P] [US2] Update `cfp/skills/_shared/preamble.md` Step 0: document `<store-error>` in the context block; `<store>` "is empty only when `<store-error>` is present"; new rule before the init offer: when `<store-error>` is present, show it with a hint to fix the named variable and stop, do not offer `/cfp:init`; update the CLI bullet to "The CLI finds the store through `--store`, `CFP_STORE`, the config file (`CFP_CONFIG_DIR`, `$XDG_CONFIG_HOME/cc-cfp`, or `~/.config/cc-cfp`), or the default `<data folder>/store`".

**Checkpoint**: SC-002 and SC-003 covered by tests.

## Phase 5: User Story 3, Personal conference profiles (P2)

**Goal**: `<data folder>/profiles` is a second seed source; user wins on a clash with a warning.
**Independent test**: an `acme-summit` profile in the data folder is seeded by init.

- [X] T011 [US3] Extend `cfp/scripts/test/test_seeds.py` and `cfp/scripts/test/test_config.py`. Library: user-only profile is seeded and approved; user `kubecon` replaces shipped `kubecon` with one warning `profile 'kubecon': using <user dir> instead of the shipped <plugin dir>`; a variant without `seed_version` adds `; it has no seed_version, so it will not replace an existing store copy`, its state over a versioned store copy is `current`, and `seed-update` refuses; a user profile without `seed_version` is seeded and its store copy then reports `local`; status entries carry `source` (`plugin`|`user`) and `seed_dir`; user diffs use `user/<rel>`; user `seed_version` later than the store copy gives `outdated` and `update` works; lower gives `newer` and `update` refuses; missing user dir is silent; folder without `profile.md` is skipped; existing `seeds.status(store, SEED_DIR)` calls keep returning a list. CLI (via `run_cli`, next to the existing seed tests): `seed-status` returns `{"seeds", "warnings"}`; `seed-update` returns `source` and `warnings`; `config init` merges seed warnings; `--user-seed-dir` overrides the folder; `seed-update` for an unknown name errors with `no seed profile '<id>' in <plugin dir> or <user dir>`; `seed-status` with `CFP_DATA_DIR=rel` fails.
- [X] T012 [US3] Implement in `cfp/scripts/cfplib/seeds.py` with these interfaces: `collect(plugin_dir, user_dir=None) -> (list[dict], list[str])` with entries `{name, dir, source}` per `data-model.md` (plugin first, user replaces same name; missing `plugin_dir` keeps the existing error; missing `user_dir` is empty); `status(store_path, seed_dir, user_dir=None) -> list` (entries gain `source`, `seed_dir`); `status_report(store_path, seed_dir, user_dir=None) -> (list, list[str])`; `update(store_path, seed_dir, profile_id, files=None, all_files=False, user_dir=None) -> dict` adding `source` and `warnings`; `_diff` labels the target `user/<rel>` for user seeds. Keep all feature 001 state semantics.
- [X] T013 [US3] Wire it in `cfp/scripts/cfplib/config.py` `init_store(store, values, seed_dir=None, user_seed_dir=None)` (seed from `collect`, result adds `warnings`; `None` means no user source) and in `cfp/scripts/cfp_store.py`: `seed-status` returns `{"seeds", "warnings"}`, `seed-update` returns `source` and `warnings`, `config init` merges seed warnings; add optional `--user-seed-dir` to all three (default `paths.user_profiles_dir()`, whose `CfpError` propagates). Make T011 pass.
- [X] T014 [US3] Update `cfp/skills/init/SKILL.md` Steps 5 and 6: collect `warnings` from `config init` and `seed-status`, show each clash once per run (de-duplicate by profile name); for `newer` with `source: user` say "the store copy's seed_version is higher than your profile's, nothing to update"; name the source of an outdated profile in the update offer.

**Checkpoint**: SC-004 covered.

## Phase 6: User Story 4, Documentation (P3)

**Goal**: no document describes Obsidian as the default store or the old resolution order.
**Independent test**: quickstart step 8 search.

- [X] T015 [P] [US4] Update `README.md`: init paragraph (default `~/.local/share/cc-cfp/store`, Obsidian vaults offered), rewrite the resolution order around line 32, and add a short "Configuration" section: store resolution order; config folder and data folder rules with `CFP_CONFIG_DIR`, `CFP_DATA_DIR`, `CFP_STORE`, `XDG_*`; personal profiles in `<data folder>/profiles` with the rules that `seed_version` is an ISO date `YYYY-MM-DD`, that a profile without it is copied once and never offered updates, and that a variant of a shipped profile needs a later `seed_version` than the shipped one.
- [X] T016 [P] [US4] Update the guide under `docs/guide/content/modules/ROOT/pages/` (AsciiDoc, one sentence per line): `overview/install.adoc` (store default around lines 85 to 87, and lines 111, 142, 156, 161, plus a configuration subsection with the T015 content); `reference/commands.adoc` (lines 56 to 57: default path rule per FR-006/FR-007, and a link to the configuration reference for the resolution order and folders); `reference/config.adoc` (fixed config path at lines 25 and 56, and the "no store configured" sentence, replaced by the full resolution order, both folders, env vars, and personal profiles); `reference/cli.adoc` (lines 50 and 130: new `config show`/`config init`/`seed-status`/`seed-update` fields and `--user-seed-dir`); `user/index.adoc` (line 61); `internals/store.adoc` (line 51); `internals/architecture.adoc` (line 104: hook imports `cfplib.paths`, `<store-error>`). Update `docs/guide/diagrams/store-model.claims.yaml` line 6 and regenerate or annotate `store-model.svg` if its label states the config path or default. Check `docs/guide/diagrams/architecture.claims.yaml` and `docs/guide/inputs.yaml` and adjust only statements about the default.
- [X] T017 [P] [US4] Annotate feature 001 artifacts with "Superseded by feature 002: the default store is `<data folder>/store` and the config folder follows XDG; see specs/002-xdg-config-store/spec.md", or adjust the example: `specs/001-cfp-plugin/spec.md` (Input line and FR-001), `plan.md` (Summary, Storage, research summary line), `research.md` (store layout rationale), `data-model.md` (line 25, fixed config location), `contracts/commands.md` (init "Asks", and the "Hook: `<cfp-context>`" section pointing to `specs/002-xdg-config-store/contracts/hook.md` for `<store-error>`), `contracts/scripts.md` (line 11, old order and "Missing store is an error"), `contracts/store-files.md` (config.json example). Do not touch `tasks.md`, `review-findings.md`, `REVIEW-CODE.md`, `SMOKE-TEST.md`, `quickstart-results.md`, `checklists/`.

## Phase 7: Polish

- [ ] T018 Run `make test`, `make test-hook`, `make lint-dashes`; fix failures.
- [ ] T019 Run quickstart.md script-level scenarios 1 to 6 and the docs search (8) in a scratch HOME under the session scratchpad; record outcomes in `specs/002-xdg-config-store/quickstart-results.md`. List scenario 7 for the user, including the `kubecon` clash check that the warning appears exactly once.

## Dependencies

- T001 before everything. T002 then T003 then T004 (Phase 2) block all stories.
- US1 (T005 to T007) and US2 (T008 to T010) are independent of each other after Phase 2; within US1, T005 before T006, T007 after T006.
- US3 (T011 to T014) depends on Phase 2 and on T006 (shared `cmd_config_init`); T014 after T007 (same skill file).
- US4 (T015 to T017) after US1 to US3 so docs describe final behavior.
- Polish last.

## Parallel Examples

- US2: T008 (test file) and T010 (preamble) touch different files.
- US4: T015, T016, T017 touch different files.

## Implementation Strategy

MVP is Phase 2 plus US1 and US2 (both P1): neutral default, XDG config, and hook parity. US3 adds personal profiles. US4 closes the docs gap. Commit after each phase.
