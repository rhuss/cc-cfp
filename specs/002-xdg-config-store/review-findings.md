# Deep Review Findings

**Date:** 2026-11-27
**Branch:** 002-xdg-config-store
**Rounds:** 3 (plus one CodeRabbit-verified skill-text fix)
**Gate Outcome:** PASS
**Invocation:** quality-gate (ship pipeline stage 7)

## Summary

| Severity | Found | Fixed | Remaining |
|----------|-------|-------|-----------|
| Critical | 0 | 0 | 0 |
| Important | 9 | 9 | 0 |
| Minor | 28 | 13 | 15 |
| Notable | 2 | - | 2 |
| **Total** | **39** | **22** | **17** |

Counts are after deduplication (42 raw findings across sources).

**Agents completed:** 5/6 (Goal Alignment skipped: no PR) + CodeRabbit (4 runs) + Codex (1 run, no actionable issues) + 3 narrowed re-review agents
**Agents failed:** none. Copilot skipped (disabled in config, CLI not installed).

## Findings

### FINDING-1
- **Severity:** Important
- **Confidence:** 90
- **File:** cfp/scripts/cfplib/config.py:117-129 (`_seed_profile`), cfp/scripts/cfplib/seeds.py (`update`)
- **Category:** security
- **Source:** security-agent (also reported by: production-readiness-agent)
- **Round found:** 1
- **Resolution:** fixed (round 1, b86ab79)

**What is wrong:**
`_seed_profile` used `shutil.copytree(..., symlinks=True)` and then rewrote `profile.md` with `frontmatter.save`, which follows symlinks. A personal profile whose `profile.md` or `events/` is a symlink (stow, chezmoi, home-manager) ended up as links in the store, and the approval stamp, later `profile approve`, `event write`, and `seed-update` calls wrote into the user's own source files.

**Why this matters:**
Silent modification of files outside the store, for example a version-controlled dotfiles profile, and a store that is no longer self-contained. Reproduced by both agents.

**How it was resolved:**
`_seed_profile` copies only the files `seeds.seed_files` lists, as regular files (a symlinked `profile.md` or profile folder is read by content; symlinked `events/` or `examples/` folders and files are skipped, matching what seed-status compares). `seeds.update` refuses before writing when the store profile folder, its subfolders, or a target file is a symlink. Tests: `test_init_store_copies_symlinked_user_profile_as_regular_files`, `test_update_refuses_to_write_through_a_symlinked_store_copy`.

### FINDING-2
- **Severity:** Important
- **Confidence:** 90
- **File:** cfp/scripts/cfplib/seeds.py:59-71 (`collect`)
- **Category:** security
- **Source:** security-agent
- **Round found:** 1
- **Resolution:** fixed (round 1, b86ab79)

**What is wrong:**
User profile names came straight from folder names without `store.check_id`. A folder like `bad name;x` was seeded, became `default_profile`, made `seed-status` fail for the whole store, and would be passed unquoted as `--profile` in skill shell commands.

**Why this matters:**
Every other store id is validated and the skills rely on that; this new input path bypassed it, enabling shell syntax in LLM-built commands and breaking the update flow.

**How it was resolved:**
`collect` validates user folder names with `store.check_id` and skips invalid ones with a warning naming the folder and the rule. Tests: `test_init_store_skips_user_folder_with_unsafe_name`, `test_collect_skips_user_folder_with_unsafe_name`.

### FINDING-3
- **Severity:** Important
- **Confidence:** 85
- **File:** cfp/scripts/cfplib/config.py (`_seed_profile`, `init_store`), cfp/scripts/cfplib/seeds.py (`_profile_status`)
- **Category:** correctness
- **Source:** correctness-agent (also reported by: production-readiness-agent, coderabbit)
- **Round found:** 1
- **Resolution:** fixed (round 1, b86ab79)

**What is wrong:**
A personal profile with broken front matter or non-UTF-8 content failed after `copytree`: the store kept an unapproved partial copy, `config.json` was never written, the error named the store copy instead of the source, a re-run reported success and skipped the broken copy, and `seed-status` failed for every profile.

**Why this matters:**
Hand-written personal profiles make this a plausible path; one typo left init half done and blocked the update check for shipped profiles too.

**How it was resolved:**
The seed's `profile.md` is parsed first (errors name the seed file); the copy is built in a hidden staging folder and renamed into place, removed on any failure. `init_store` skips a failing user profile with a warning and continues, so the config is saved; a broken shipped seed still raises. `_profile_status` reports `unreadable` for a broken seed. Tests: `test_init_store_skips_broken_user_profile_without_partial_copy`, `test_broken_shipped_seed_still_fails_without_partial_copy`.

**External tool analysis (CodeRabbit):**
> If a personal `profile.md` has malformed front matter, `_seed_profile` copies its directory before parsing fails. If the user fixes the personal source and retries, Line 157 skips the retained directory. Initialization then succeeds with the malformed store copy. Seed status reports `unreadable`, which `seeds.update` cannot repair. Stage the copy and approval changes in a temporary directory. Publish the target directory only after validation succeeds, and remove the temporary directory on failure.

### FINDING-4
- **Severity:** Important
- **Confidence:** 88
- **File:** cfp/hooks/scripts/context-hook.py:57-62
- **Category:** correctness
- **Source:** re-review agent (round 1)
- **Round found:** 2
- **Resolution:** fixed (round 2, a356f3e; message refined in round 3, 0035081)

**What is wrong:**
The round 1 guard caught `OSError` from `Path.is_file()`, but since Python 3.14 `is_file()` returns `False` on a `PermissionError`. With the system `python3` (3.15) an inaccessible store showed as uninitialized with no error.

**Why this matters:**
The skill would offer `/cfp:init` on an existing store instead of reporting the access problem.

**How it was resolved:**
The hook uses `os.stat`: not-found means not initialized, any other `OSError` gives `<store-error>cannot access <path>: <reason>` with an empty `<store>`. Verified under Python 3.12 and 3.15. Tests: `test_unreadable_store_yields_store_error` and the in-process `test_store_check_does_not_rely_on_path_is_file`. contracts/hook.md documents the case.

### FINDING-5
- **Severity:** Important
- **Confidence:** 80
- **File:** cfp/scripts/cfplib/seeds.py (`_file_states`)
- **Category:** correctness
- **Source:** re-review agent (round 1)
- **Round found:** 2
- **Resolution:** fixed (round 2, a356f3e)

**What is wrong:**
After round 1, a broken seed `profile.md` was handled, but an unreadable seed event or example file still made `seeds.status()` raise for the whole listing.

**Why this matters:**
One bad event file in a personal profile blocked the update check for all profiles, including shipped ones.

**How it was resolved:**
Seed files that cannot be read get the file state `unreadable` with an `error`. Test: `test_unreadable_seed_event_is_reported_and_refused`.

### FINDING-6
- **Severity:** Important
- **Confidence:** 95
- **File:** cfp/scripts/cfplib/seeds.py (`_file_states`, `update`)
- **Category:** correctness
- **Source:** re-review agent (round 2)
- **Round found:** 3
- **Resolution:** fixed (round 3, 0035081)

**What is wrong:**
An unreadable seed file that the store lacked was reported as `missing` (the store check ran first), so `update --all` wrote `profile.md` and then failed on that file, leaving the update half applied and the profile marked current.

**Why this matters:**
Violates the "nothing is written when the call is refused" rule; the skipped file would never be offered again.

**How it was resolved:**
`_file_states` reads the seed side first; `update` loads every chosen seed file before the first write. Tests: `test_unreadable_seed_file_missing_from_store_is_not_offered`, `test_update_loads_every_seed_file_before_writing`.

### FINDING-7
- **Severity:** Important
- **Confidence:** 85
- **File:** cfp/skills/init/SKILL.md (Step 6) and cfp/scripts/cfplib/seeds.py (`update`)
- **Category:** production-readiness
- **Source:** re-review agent (round 2)
- **Round found:** 3
- **Resolution:** fixed (round 3, 0035081)

**What is wrong:**
After round 2, `seed-update --all` refused whenever any file was unreadable, while the skill still mapped "update everything shown" to `--all`.

**Why this matters:**
The obvious user choice produced a CLI error with no recovery path.

**How it was resolved:**
`--all` now takes every takeable file and lists unreadable ones under `skipped`; naming an unreadable file in `--files` refuses. The skill explains this. cli.adoc updated.

### FINDING-8
- **Severity:** Important
- **Confidence:** 75
- **File:** cfp/scripts/cfplib/config.py (`_seed_profile`)
- **Category:** external
- **Source:** coderabbit
- **Round found:** 2 (CodeRabbit run on round 1 fixes)
- **Resolution:** fixed (round 3, 0035081)

**What is wrong:**
The staging folder name `.<id>.seeding` was fixed, so two concurrent inits could delete each other's staging folder and publish an incomplete copy.

**Why this matters:**
A published but incomplete profile carries the current version and is never repaired.

**How it was resolved:**
Each call uses a unique `tempfile.mkdtemp` folder in `profiles/`, chmod'ed to the profiles folder's mode, removed on failure. Hidden folders are ignored by `store.list_profile_ids`, so a leftover from a killed run never becomes a profile. Test: mode and no-leftover assertions in `test_init_store_copies_symlinked_user_profile_as_regular_files`, `test_hidden_staging_folder_is_not_a_profile`.

**External tool analysis (CodeRabbit):**
> Two concurrent initializations can pass the target check before either publishes `acme`. If A finishes copying auxiliary files, B can delete A's staging directory and start another copy. A can then save `profile.md` and publish B's incomplete directory. Create a unique sibling directory for each call and clean up only that directory.

### FINDING-9
- **Severity:** Important
- **Confidence:** 75
- **File:** cfp/skills/init/SKILL.md:89
- **Category:** external
- **Source:** coderabbit
- **Round found:** 3 (CodeRabbit run on rounds 2 and 3)
- **Resolution:** fixed (after round 3, c76e780; CodeRabbit re-run on that commit is clean)

**What is wrong:**
After "update everything shown" with unreadable files left out, the profile is current and the skipped files are never offered again; the skill did not say so.

**Why this matters:**
The user loses the chance to take the fixed file through the update flow.

**How it was resolved:**
The skill recommends `skip`, fixing the file, and rerunning `/cfp:init`, and its update notes explain how to take a skipped file later.

**External tool analysis (CodeRabbit):**
> If the user selects `update everything shown`, the command skips unreadable files but replaces `profile.md`. The profile then becomes current, so fixing the unreadable file and rerunning `/cfp:init` does not offer its update. Tell the user to fix unreadable files before updating, or provide a recovery procedure for skipped files.

### Fixed Minor findings

| Source | File | Finding | Fix |
|--------|------|---------|-----|
| correctness | cfp/scripts/cfp_store.py `_cfp_store_warning` | A relative CFP_STORE got the "overrides" warning | Separate warning naming the error (b86ab79) |
| production | context-hook.py | `is_file()` outside the try could crash the hook | Guarded (b86ab79), then os.stat (a356f3e) |
| architecture | internals/architecture.adoc | Store error described as eager | Lazy wording (24d0c45) |
| architecture | init/SKILL.md Step 7 | `config show` values missing on "keep it as it is" | Step 1 runs `config show` (24d0c45) |
| architecture | init/SKILL.md | Personal seed files called "shipped" | Wording (24d0c45) |
| re-review r1 | config.py, store.py | Leftover staging folder could become default profile | Hidden folders ignored (a356f3e) |
| re-review r1 | _shared/preamble.md | Store error description and hint only for variables | Two hints (a356f3e, 0035081) |
| re-review r1 | install/cli/config.adoc | Symlinked folders not mentioned | Wording (a356f3e) |
| re-review r2 | test_hook.py | Permission test passed without the fix on 3.12 | In-process test patches `Path.is_file` (0035081) |
| re-review r2 | contracts/hook.md, hook docstring | Inaccessible config.md case undocumented | Documented (0035081) |
| re-review r2 | preamble, hook | "cannot read" for a stat error | "cannot access" (0035081) |
| re-review r2 | seeds.py docstrings | `unreadable` state missing | Documented (0035081) |
| coderabbit r2 | init/SKILL.md Step 6 | Repaired profile not copied after "keep it as it is" | `missing` handling (0035081) |

## Notable Observations

### NOTABLE-1
- **File:** README.md:34-56 (and install.adoc, config.adoc, commands.adoc, paths.py/config.py/context-hook.py docstrings, preamble.md)
- **Category:** architecture
- **Source:** architecture-agent
- **Description:** The folder and variable rules are written out in about eight places, and copies have already drifted once (fixed).
- **Rationale:** Every rule change needs manual edits in all copies; source-verification comments track files, not semantic equality. A single reference page with links would reduce drift.

### NOTABLE-2
- **File:** cfp/scripts/test/conftest.py:23-38
- **Category:** test-quality
- **Source:** test-quality-agent
- **Description:** HOME/XDG/CFP isolation is opt-in through fixtures.
- **Rationale:** Already captured in the idea inbox as `autouse-home-isolation` (feature 001); not added again.

## Goal Alignment

Skipped (no PR found for the branch).

## Post-Fix Spec Coverage

The fix loop replaced the `copytree` seeding and removed a few lines. All 19 functional requirements were re-checked against the code after round 3: resolution (FR-001 to FR-005, FR-009) in `paths.py`, init and `config show` (FR-006 to FR-008a, FR-011) in `cfp_store.py`, `config.py`, and the init skill, seeds (FR-010 to FR-014) in `seeds.py`, voice (FR-015) unchanged, docs (FR-016, FR-017). All spec requirements verified after fix loop.

## Test Suite Results

| Round | Test Command | Exit Code | Failures | Status |
|-------|-------------|-----------|----------|--------|
| 0 (before review) | make test | 0 | 0 | passed (330) |
| 1 | make test | 0 | 0 | passed (336) |
| 2 | make test | 0 | 0 | passed (339) |
| 3 | make test | 0 | 0 | passed (342) |
| final | make test, make test-hook, make lint-dashes | 0 | 0 | passed |

Test suite passed in all fix rounds.

## Remaining Findings

All remaining findings are Minor; none block the gate.

| Source | File | Finding |
|--------|------|---------|
| architecture | cfp/scripts/cfplib/config.py | `user_config_path`, `load_user_config` used only by tests; `resolve_store_with_source` is a pass-through |
| architecture | cfp/scripts/cfplib/seeds.py | `status` (test-only) carries the docs, `status_report` is the one used |
| architecture | cfp/scripts/cfp_store.py | One concept, five names (`user_seed_dir`, `user_profiles_dir`, `user_dir`); `_cfp_store_warning` re-parses CFP_STORE |
| architecture | cfp/scripts/cfplib/paths.py | Module docstring says every function takes `env` and `home`; "feature 001 location" jargon |
| architecture | cfp/scripts/cfp_store.py | `paths.config_file()` called only for its validation side effect; store path normalized three times |
| security | cfp/skills/init/SKILL.md | Paths in `--store "<path>"` rely on double quotes; no single-quote escaping rule for the LLM |
| production | cfp/scripts/cfplib/paths.py | A malformed config file silently falls back to the default store; no `config_error` in `config show` or the hook |
| production | cfp/scripts/cfplib/config.py | `write_user_config` is not atomic (store files are) |
| production | cfp/skills/_shared/preamble.md | "Pass --store only when it differs" cannot be followed; hook and Bash env can differ |
| test-quality | test_cli_foundation.py | CLI-level tests missing for relative CFP_STORE on normal commands, `--store` bypassing broken variables, `config show` with bad CFP_CONFIG_DIR |
| test-quality | test_seeds.py | User-seed update approval test cannot tell store flag from seed flag |
| test-quality | test_seeds.py | No end-to-end CLI test that `CFP_DATA_DIR` beats `XDG_DATA_HOME` for seeding |
| test-quality | test_cli_foundation.py | No test that init with a non-default store leaves the data folder absent |
| re-review r3 | cfp/scripts/cfplib/config.py | The second of two concurrent inits fails at `os.replace` (no corruption, but an error or misleading warning) |
| re-review r3 | cfp/scripts/cfplib/config.py | Unique staging folders left by SIGKILL are never cleaned up (hidden, ignored by listings) |
