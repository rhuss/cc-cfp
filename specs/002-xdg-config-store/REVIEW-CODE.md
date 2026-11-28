# Code Review: XDG Configuration and Neutral Store Default

**Spec:** specs/002-xdg-config-store/spec.md
**Contracts:** specs/002-xdg-config-store/contracts/
**Date:** 2026-11-27
**Reviewer:** Claude (speckit-spex-gates-review-code, ship pipeline stage 7)

## Compliance Summary

**Overall Score: 100%** (97% before the one fix below)

- Functional Requirements: 19/19 (100%, FR-016 fixed in 9b32259)
- Edge Cases: 11/11 (100%)
- Success Criteria: 5/5 (100%)

Acceptance scenarios of User Stories 1 to 4 are covered by the requirements above. The CLI-testable parts have tests. The skill-driven parts (US1 scenario 3 vault choices, the absolute default path, FR-012 "each clash shown once per run") are specified in `cfp/skills/init/SKILL.md` and need a manual check.

## Detailed Review

### Functional Requirements

| Req | Implementation | Status |
|-----|----------------|--------|
| FR-001 config folder order | `cfp/scripts/cfplib/paths.py` `config_dir`, `config_file` | Compliant |
| FR-002 XDG and CFP_* validation, lazy errors | `paths.py` `_cfp_var`, `_xdg_var`, `resolve_store`; `cfp_store.py` `user_seed_dir`, `cmd_config_init` | Compliant |
| FR-002a hook store error, preamble | `cfp/hooks/scripts/context-hook.py`; `cfp/skills/_shared/preamble.md` Step 0.3 | Compliant |
| FR-003 legacy fallback | `paths.py` `read_config` | Compliant |
| FR-004 shared resolver | hook imports `cfplib.paths`; `config.resolve_store` delegates | Compliant |
| FR-005 store order and default | `paths.resolve_store`, `default_store` | Compliant |
| FR-006 init default from resolution | `SKILL.md` Step 1 via `config show` | Compliant |
| FR-007 no Obsidian default, up to 3 vaults | `SKILL.md` Step 1 | Compliant |
| FR-008 create store, save config, CFP_STORE warning | `config.init_store`, `write_user_config`; `cfp_store._cfp_store_warning` | Compliant |
| FR-008a `config show` fields | `cfp_store.cmd_config_show` | Compliant |
| FR-009 data folder order | `paths.data_dir` | Compliant |
| FR-010 second seed source | `seeds.collect` | Compliant |
| FR-011 both sources, no folder creation, report path | `cfp_store.user_seed_dir`; `config.init_store`; `SKILL.md` Step 7 | Compliant |
| FR-012 clash warnings, once per init | `seeds.collect`; `SKILL.md` Steps 5 and 6 de-duplicate | Compliant |
| FR-013 feature 001 seed rules, guide statements | `seeds._profile_status`, `seeds.update`; install.adoc, config.adoc | Compliant |
| FR-014 `source` and `seed_dir` per seed | `seeds._entry_status` | Compliant |
| FR-015 no cfp voice folder | `SKILL.md` Step 3 unchanged | Compliant |
| FR-016 docs describe defaults, order, folders, personal profiles | README, install.adoc, commands.adoc | Compliant after 9b32259 (commands reference lacked the folder variables and personal profiles) |
| FR-017 Obsidian default statements updated or annotated | README, guide, SKILL.md, feature 001 spec/plan/research/contracts | Compliant |

### Error Handling and Edge Cases

All 11 edge cases of the spec are handled and tested: empty or relative XDG values ignored; relative `CFP_*` rejected with the variable name; relative `--store` resolved against the current folder; the default store is created by init only; a malformed config or one without `store` gets no legacy fallback; folders without `profile.md` are skipped; the `newer` state applies to a lower user version; a variant without `seed_version` never replaces a store copy; at most three vaults; seed-update works for user-only profiles; a missing user folder is never an error.

### Extra Features (Not in Spec)

- `--user-seed-dir` hidden test argument: required by contracts/cli.md.
- Added in the deep review, as hardening of FR-010/FR-011 input handling: invalid profile folder names are skipped with a warning; unreadable personal profiles are skipped with a warning; the `unreadable` file state in seed-status; `<store-error>` for an inaccessible `config.md` (contracts/hook.md updated). These are candidates for a short spec note (see below).

### Spec-Declared Constants

The spec has no `## Constants` section; check skipped.

## Code Quality Notes

See the Deep Review Report below and `review-findings.md`.

## Recommendations

### Critical (Must Fix)

None.

### Spec Evolution Candidates

- FR-002a covers resolution failures only; the hook now also reports an inaccessible `config.md` as `<store-error>`. contracts/hook.md documents it; the spec text could mention it.
- FR-010/FR-011 could state the profile name rule and that unreadable or invalid personal profiles are skipped with a warning.

### Optional Improvements

Remaining Minor findings are listed in `review-findings.md`.

## Deep Review Report

Deep review completed.

Gate: PASS (after fix round 3, plus one skill-text fix verified by CodeRabbit)

Review Agents:

| Agent                   | Found | Fixed | Remaining | Status    |
|-------------------------|-------|-------|-----------|-----------|
| Correctness             |     2 |     2 |         0 | completed |
| Architecture & Idioms   |     9 |     3 |         6 | completed |
| Security                |     3 |     2 |         1 | completed |
| Production Readiness    |     6 |     3 |         3 | completed |
| Test Quality            |     5 |     0 |         5 | completed |
| Goal Alignment          |     0 |     0 |         0 | skipped (no PR found) |
| CodeRabbit (external)   |     4 |     4 |         0 | completed (4 runs, last run clean) |
| Copilot (external)      |     0 |     0 |         0 | skipped (disabled in config, CLI not installed) |
| Codex (external)        |     0 |     0 |         0 | completed (no actionable issues) |
| Re-review agents (r1-r3)|    13 |    11 |         2 | completed |
| Test Suite (regression) |     0 |     0 |         0 | passed (342 tests after round 3) |
|-------------------------|-------|-------|-----------|-----------|
| Total                   |    42 |    25 |        17 |           |

Counts above are per source before deduplication. After merging duplicates: 0 Critical, 9 Important (9 fixed), 28 Minor (13 fixed, 15 remaining), 2 Notable. The "Remaining" column holds Minor and Notable items only.

Agent Leaderboard MVP: Architecture & Idioms (9 findings)

Key fixes applied:
  1. Personal profiles are copied as regular files; seed-update refuses to write through symlinks, so store writes never change the user's own files (security, production)
  2. Profile folder names that are not valid ids are skipped with a warning before they reach store paths or skill shell arguments (security)
  3. A broken personal profile is skipped with a warning naming the source file; seeding uses a unique staging folder, so no partial copy remains and init still saves the config (correctness, production, coderabbit)
  4. seed-status reports unreadable seeds and seed files instead of failing for every profile; seed-update loads every file before writing, so unreadable seed files refuse the update before any write, but a store write that fails after the first write can leave earlier files updated (re-review r1, r2)
  5. The context hook uses os.stat, so an inaccessible store gives `<store-error>` on Python 3.14+ too (production, re-review r1)
  6. config init warns separately about an invalid CFP_STORE (correctness)
  7. Init skill: config show on "keep it as it is", new warning kinds, unreadable files and `--all`, re-run setup for a still-missing profile, skipped files not offered again (architecture, re-review, coderabbit)
  8. Guide and contract text: lazy resolution wording, profile name rule, symlink handling, `cannot access` store error (architecture, re-review)
  9. Commands reference names both folders, their variables, and personal profiles (spec compliance FR-016)

Post-fix spec coverage: 19/19 functional requirements verified (all covered)

Notable observations: 1 captured to brainstorm/idea-inbox.md (1 already there from feature 001)

Details: specs/002-xdg-config-store/review-findings.md

Fix commits: 9b32259 (spec compliance), b86ab79 and 24d0c45 (round 1), a356f3e (round 2), 0035081 (round 3), c76e780 (CodeRabbit round 3 finding)
