# Code Review: CFP and Bio Plugin for Conference Submissions

**Spec:** specs/001-cfp-plugin/spec.md
**Contracts:** specs/001-cfp-plugin/contracts/
**Date:** 2026-10-09
**Reviewer:** Claude (speckit-spex-gates-review-code, ship pipeline stage 7)

## Compliance Summary

**Overall Score: 100%** (99% before the one fix below)

- Functional Requirements: 43/43 (100%)
- Acceptance Scenarios: 24/24 (100%, one fixed in 7a93a14)
- Edge Cases: 13/13 (100%)
- Non-Functional (Success Criteria testable at the CLI): 8/8 (100%)

## Detailed Review

### Functional Requirements

| Requirement | Implementation | Status |
|---|---|---|
| FR-001 markdown store in configurable folder, Obsidian default | cfplib/frontmatter.py, config.py; skills/init Step 1 | Compliant |
| FR-002, FR-002a speaker, voice, rounds in store config; store path in user config | cfplib/config.py (config.md, ~/.config/cc-cfp/config.json) | Compliant |
| FR-003 hand-editable, tolerant of valid edits | frontmatter.py preserves unknown keys; list_dir reports and skips broken files | Compliant |
| FR-004 profile contents and verification statuses | knowledge-base/profiles/kubecon/profile.md; profile.validate (unverified, page, screenshot) | Compliant |
| FR-005 per-event overrides applied on top | profile.effective (merge by id, tracks, submission_limit) | Compliant |
| FR-006 shipped KubeCon profile, EU 2027 and NA 2026, five criteria, hard rules, unverified limits, approved | profile.md and events/*.md; config._seed_profile sets approved | Compliant |
| FR-007, FR-008 profile research, screenshots as paths or pasted | skills/profile new and refresh, verification labels | Compliant |
| FR-009 approval per profile and override; manual entry approved | proposals.create checks is_approved; event write takes approved from JSON; draft Step 1 manual entry sets approved | Compliant |
| FR-010, FR-010a refresh creates override, asks before family change; inline event creation | skills/profile refresh Step 4; skills/draft Step 1 | Compliant |
| FR-011 talk story fields | cfplib/talks.py sections and meta lists | Compliant |
| FR-012 four input sources | skills/draft Step 3 | Compliant |
| FR-013, FR-014 one question at a time, session type limits and refusal | preamble, draft Step 2 | Compliant |
| FR-015 two or three angles | draft Step 5, guidance/abstract-angles.md | Compliant |
| FR-016, FR-017 every field, benefits not restating | draft Step 6, guidance/benefits-field.md, reviewer step 7 | Compliant |
| FR-018, FR-019 committee review scoring, rejection reasons as reference | review.py packet and record; agents/committee-reviewer.md | Compliant |
| FR-020 revise loop, configurable rounds default 3 | draft Step 7; config review_rounds default 3 | Compliant |
| FR-021, FR-021a voice pass after pass, skip without prose plugin, order voice, pre-flight, paste view | draft Steps 8 to 12 | Compliant |
| FR-022 paste view with counts, flags, shorten first | pasteview.py; draft Step 9 | Compliant |
| FR-023 save every step, resumable | every step calls the CLI; draft Resuming section | Compliant |
| FR-024, FR-025 bio and resource management | bios.py, skills/bio | Compliant (type names blog and session are short forms) |
| FR-026, FR-027 bio snapshot, resources with recording first | proposals.set_meta and set_bio_text; draft Step 6 | Compliant |
| FR-028, FR-028a hard rules and status counting; in-flow and standalone | preflight.py, lifecycle.count_submissions; draft Step 10, skills/check | Compliant |
| FR-029, FR-030 audience level warning; rule citation and severity | preflight.add_finding; skills/check Step 4; findings carry rule, severity, source | Compliant |
| FR-031, FR-031a statuses and dates; automatic and manual ready | lifecycle.py, ready_check, --force | Compliant |
| FR-032 status change with date, grouped list | lifecycle.set_status, proposals.list_proposals, skills/status | Compliant (profile column added in 7a93a14) |
| FR-033, FR-034 accepted adds example, presented records outing | lifecycle._add_accepted_example, _record_outing | Compliant |
| FR-035 rejected or withdrawn as input source | draft Step 3 option 4; status reopen | Compliant |
| FR-036 to FR-038 nothing submitted, no co-speaker bios, no slides | no such code paths; preamble rules | Compliant |

### Error Handling and Edge Cases

All 13 edge cases in the spec are implemented: missing store (preamble Step 0), no limit (counts no-limit), unverified limits labeled approximate (pasteview), existing material (draft Step 3), resume (draft Resuming), review never passes (draft Step 7 end), research finds nothing (profile skill), screenshots win (profile Step 4), deadline passed (draft Step 1 warning), missing override (FR-010a), prose plugin missing (draft Step 8), invalid front matter reported and skipped (store.list_dir), co-located event limits (profile.effective field_overrides).

### Extra Features (Not in Spec)

- `proposal set-meta --session-type` and `--co-speaker-genders`, `config init --default-profile`, `status set --force`: additive CLI conveniences that serve FR-014, FR-028, and FR-031a. Recorded in the contract. Not scope creep.
- `review_stale` and automatic demotion of an edited `ready` proposal (added by the deep review): keeps FR-031a truthful. Recorded in the contract.

### Spec-Declared Constants

The spec has no `## Constants` section; the check was skipped.

## Code Quality Notes

See the Deep Review Report below. The code is small, stdlib only, and well tested; the issues found were in rule edge cases, the hand-written YAML parser, and shell-argument hygiene in the skills.

## Recommendations

### Critical (Must Fix)

None remaining.

### Spec Evolution Candidates

- FR-030: decide whether "a previously-presented note exists" or "the note explains significant differences" downgrades the repeat rule (NOTABLE-1 in review-findings.md).
- Lifecycle: the spec does not say what happens to a `ready` proposal that is edited; the implementation now demotes it to draft with stale checks. Worth a one-line clarification.

### Optional Improvements

The 17 Minor and 11 Notable items in review-findings.md.

## Deep Review Report

Deep review completed.

Gate: PASS (after fix round 3)

Review Agents:

| Agent                   | Found | Fixed | Remaining | Status    |
|-------------------------|-------|-------|-----------|-----------|
| Correctness             |     8 |     4 |         4 | completed |
| Architecture & Idioms   |    19 |     9 |        10 | completed |
| Security                |     8 |     6 |         2 | completed |
| Production Readiness    |    11 |     6 |         5 | completed |
| Test Quality            |    13 |     6 |         7 | completed |
| Goal Alignment          |     0 |     0 |         0 | skipped (no PR, no git remote) |
| CodeRabbit (external)   |     8 |     5 |         1 | completed (2 dismissed, 3 runs) |
| Copilot (external)      |     0 |     0 |         0 | skipped (disabled in config, CLI not installed) |
| Codex (external)        |     0 |     0 |         0 | failed (usage limit until 2026-10-17) |
| Re-review agents (r2,r3)|     7 |     5 |         2 | completed |
| Test Suite (regression) |     0 |     0 |         0 | passed (149 tests in round 3) |
|-------------------------|-------|-------|-----------|-----------|
| Total                   |    74 |    41 |        31 |           |

Counts above are per source before deduplication; after merging duplicates the totals are 0 Critical, 15 Important (13 fixed, 2 dismissed with reasons), 45 Minor (28 fixed), 12 Notable (1 fixed). The "Remaining" column holds Minor and Notable items only.

Agent Leaderboard MVP: Architecture & Idioms (19 findings)

Key fixes applied:
  1. All-men rule treats "unknown" as unknown and "male" as man; event override submission limit applied (correctness)
  2. ready to draft and accepted to withdrawn transitions; edits on a ready proposal demote it and mark the review stale (architecture, coderabbit)
  3. Lifecycle reuses the proposal and talk loaders; hand-removed id no longer crashes (architecture, correctness)
  4. Skills and the reviewer agent treat fetched pages, screenshots, and packet text as data; profile research stays on the CFP host (security)
  5. Free text goes through --from-json on set-meta and add-finding instead of shell arguments (security)
  6. Inline YAML comments stripped and quoted on write; comments before nested blocks parse (production, re-review)
  7. Catch-all JSON error; non-UTF-8 and OS errors reported as problems; non-integer limits tolerated (production, security)
  8. Atomic saves with per-process temp file, symlink resolution, and file mode preserved (production, coderabbit, re-review)
  9. Unreadable proposal files produce a pre-flight warning and problems list; conflict copies counted once (test, correctness, production)
  10. Path traversal closed in profile listings; bio skill gets Write; seed copy keeps symlinks as links; config.md body preserved (security, correctness)

Post-fix spec coverage: 43/43 requirements verified (all covered)

Notable observations: 11 captured to brainstorm/idea-inbox.md

Details: specs/001-cfp-plugin/review-findings.md

Fix commits: 7a93a14 (spec compliance), c380a2a (deep review rounds 1 to 3)
