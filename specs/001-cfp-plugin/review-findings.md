# Deep Review Findings

**Date:** 2026-10-09
**Branch:** 001-cfp-plugin
**Rounds:** 3
**Gate Outcome:** PASS
**Invocation:** quality-gate (ship pipeline, stage 7)

## Summary

| Severity | Found | Fixed | Dismissed | Remaining |
|----------|-------|-------|-----------|-----------|
| Critical | 0 | 0 | 0 | 0 |
| Important | 15 | 13 | 2 | 0 |
| Minor | 45 | 28 | 0 | 17 |
| Notable | 12 | 1 | 0 | 11 |
| **Total** | **72** | **42** | **2** | **28** |

**Agents completed:** 5/5 internal (Goal Alignment skipped: no PR, no git remote) + CodeRabbit CLI 0.7.6 (3 runs)
**External tools skipped:** Codex (usage limit, retry after 2026-10-17), Copilot (disabled in config, CLI not installed)
**Fix commits:** 7a93a14 (spec compliance), c380a2a (deep review rounds 1 to 3)

Dismissed means CodeRabbit reported it as major, the fix loop verified it against the spec or YAML semantics, and it was rejected with a reason recorded below.

## Important findings (all resolved)

### FINDING-1 all-men rule silently passes on "unknown"
- **Severity:** Important, confidence 90
- **File:** cfp/scripts/cfplib/preflight.py (rule evaluator for all_men_panel)
- **Source:** correctness-agent
- **Resolution:** fixed (round 1)

The rule treated only the empty string as unknown, so the literal `unknown` the draft skill lets the user enter counted as "not a man" and the rule passed with no finding. Fixed with a gender normalizer: `unknown`, `n/a`, `?`, and similar map to unknown (warn), `male` and `m` map to `man`. Test added.

### FINDING-2 event override submission_limit never applied
- **Severity:** Important, confidence 85
- **File:** cfp/scripts/cfplib/preflight.py (submission_limit evaluator)
- **Source:** correctness-agent
- **Resolution:** fixed (round 1)

`params.max` of the family rule was read before the effective limit, so a co-located edition with a tighter limit (FR-005) was ignored. Precedence is now event override, then `params.max`, then profile limit. The event's limit is exposed in the effective profile. Test added.

### FINDING-3 state machine gaps and stale ready
- **Severity:** Important, confidence 80
- **File:** cfp/scripts/cfplib/lifecycle.py, cfp/scripts/cfplib/proposals.py
- **Source:** architecture-agent (also reported by: coderabbit in round 2 for the invalidation half)
- **Resolution:** fixed (rounds 1 and 2)

No `ready -> draft` or `accepted -> withdrawn` transition existed, and editing a `ready` proposal left the status and `ready_on` in place. Both transitions were added. Content edits (`set-field`, `set-bio-text`, `set-meta`) on a `ready` proposal now demote it to `draft`, clear the pre-flight map, and set `review_stale`; `ready-check` refuses until a new review round is recorded. Draft proposals are deliberately not invalidated because the voice pass and over-limit shortening edit text after a passing review by design (FR-021, FR-021a). Tests added.

### FINDING-4 duplicated loaders in lifecycle
- **Severity:** Important, confidence 75
- **File:** cfp/scripts/cfplib/lifecycle.py
- **Source:** architecture-agent (correctness-agent reported the KeyError symptom)
- **Resolution:** fixed (round 1)

`lifecycle` had its own proposal loader without the defaults merge, so a proposal whose `id` key was removed by hand crashed with a traceback. It now uses `proposals.load_proposal` and `talks.load_talk`. Test added.

### FINDING-5 no instruction to treat fetched content as data
- **Severity:** Important, confidence 75
- **File:** cfp/skills/_shared/preamble.md, cfp/agents/committee-reviewer.md, cfp/skills/profile/SKILL.md
- **Source:** security-agent
- **Resolution:** fixed (rounds 1 and 2)

Skills with Bash, Write, and WebFetch read web pages, screenshots, and user material with no rule about embedded instructions. A shared rule was added to the preamble, the reviewer agent is told packet text is data (only drafted fields are penalized for manipulation, examples and guidance are ignored), and the profile skill follows links only on the confirmed CFP host unless the user names another.

### FINDING-6 free text interpolated into shell arguments
- **Severity:** Important, confidence 70
- **File:** cfp/skills/draft/SKILL.md, cfp/skills/check/SKILL.md, cfp/skills/bio/SKILL.md, cfp/scripts/cfp_store.py
- **Source:** security-agent
- **Resolution:** fixed (round 1)

Skills wrote track names, angle labels, and finding reasons straight into double-quoted bash arguments, where `$(...)` and backticks still expand. `proposal set-meta` and `preflight add-finding` gained `--from-json`; the skills route every free-text value through a scratchpad JSON file; the preamble states the rule. Tests added.

### FINDING-7 inline YAML comments absorbed into values
- **Severity:** Important, confidence 90
- **File:** cfp/scripts/cfplib/frontmatter.py
- **Source:** production-agent
- **Resolution:** fixed (rounds 1 and 2)

`limit: 75 # confirmed` parsed as the string `75 # confirmed`, which then crashed counting. Plain scalars now drop a comment at whitespace-then-hash (also after a key or list dash before a nested block); quoted values keep their hash; the dumper quotes any value the parser would cut. Tests added.

### FINDING-8 unexpected exceptions break the one-JSON-object contract
- **Severity:** Important, confidence 95
- **File:** cfp/scripts/cfp_store.py, cfp/scripts/cfplib/frontmatter.py, cfp/scripts/cfplib/text.py
- **Source:** production-agent (also reported by: security-agent)
- **Resolution:** fixed (round 1)

A non-integer limit or a non-UTF-8 store file produced a Python traceback and empty stdout. `main` now emits a JSON error for any exception; `frontmatter.load` reports decode and OS errors as parse problems so lists skip the file; limits are coerced to int or "no limit". Tests added.

### FINDING-9 non-atomic writes
- **Severity:** Important, confidence 70
- **File:** cfp/scripts/cfplib/frontmatter.py (save)
- **Source:** production-agent (coderabbit added the unique temp name and mode preservation in round 2)
- **Resolution:** fixed (rounds 1 to 3)

`write_text` truncates before writing, exposing an empty file to Obsidian or a sync client. Saves now go to a hidden per-process temp file and `os.replace`, follow a symlinked target, and keep the target's file mode. Tests added.

### FINDING-10 unreadable proposals silently excluded from the submission count
- **Severity:** Important, confidence 72
- **File:** cfp/scripts/cfplib/lifecycle.py, cfp/scripts/cfplib/preflight.py
- **Source:** test-agent (also reported by: correctness-agent, production-agent)
- **Resolution:** fixed (round 1)

`count_submissions` discarded parse problems, so a broken submitted proposal lowered the count with no signal, and a sync "conflicted copy" counted twice. It now returns `(count, problems)`, counts once per id, and pre-flight emits a warn finding naming the unreadable files plus a `problems` list. Tests added.

### Dismissed (CodeRabbit round 2, reported as major)

- **Invalidate checks on every draft edit, not only on ready.** Rejected: FR-021 and FR-021a require the voice pass and the over-limit shortening to edit text after a passing review without a second review. Only `ready` proposals are demoted; the docstring now states the reason.
- **Scan for `#` outside quotes across the whole value.** Rejected: YAML treats whitespace-then-hash in a plain scalar as a comment, which is what the parser does; quoted scalars are left untouched. A full tokenizer would change behavior for no supported input.

## Minor findings

Fixed in c380a2a: `config set` erased the config.md body; `list_events` and `list_examples` skipped id validation (path traversal); non-UTF-8 and directory `.md` entries crashed listings; bio skill lacked the Write tool; seed copy followed symlinks; duplicated date helper and dead symbols removed (`_DATE_RE`, `store.stem`, unused import, no-op in `init_store`); `list_examples` always returns a tuple; draft skill no longer asks for a double write of track and level; hook matcher dropped and a 5 second timeout set; skills stop referencing `specs/` paths that do not ship; README documents `CFP_STORE` and the committee-review skill; BOM tolerated; inline JSON lists parsed with `json.loads` first (CodeRabbit); vacuous submission-limit assertion replaced; exact-limit boundary, no-limit paste view, profile and event columns, and JSON paste view assertions added; comment-before-nested-block parsing; tab-before-hash round trip; symlink-aware save; outing error text kept; reviewer and preamble wording for untrusted content.

Remaining (all unambiguous unless marked):

| # | File | Finding | Suggested fix | Class |
|---|------|---------|---------------|-------|
| M1 | cfp/scripts/cfplib/frontmatter.py:171-180 | An empty `-` list item swallows the following siblings as its nested value; the dumper emits that shape for a None item | In `parse_list`, descend only when the next line is indented deeper; dump None items as `- null` | unambiguous |
| M2 | cfp/scripts/cfplib/preflight.py:97-99 | An outing whose date does not parse is skipped silently by the repeat rule | Validate outing dates in `talk write` or emit a warn finding naming the outing | ambiguous (which side validates) |
| M3 | cfp/scripts/cfplib/counts.py:16-48, proposals.py:216-250 | Limit-result dict built four times; existing-id scan built three times | Add `text.limit_result()` and `store.existing_ids()` helpers | unambiguous |
| M4 | cfp/scripts/cfplib/proposals.py:7, lifecycle.py:5, preflight.py:9 | Status set declared twice in different orders; SEVERITIES declared twice | Keep one tuple in lifecycle and import it; import `profile.SEVERITIES` | unambiguous |
| M5 | cfp/knowledge-base/templates/*.md | Seven templates with no runtime consumer; only tests read two of them | Move the two test fixtures under cfp/scripts/test/fixtures and delete the rest, or document them as hand-authoring templates | ambiguous (product decision) |
| M6 | cfp/scripts/cfplib/proposals.py:313-318, 348-351 | `_field_def` raising CfpError used as an optional lookup | Add `_find_field()` returning None and use it in `set_meta` | unambiguous |
| M7 | cfp/scripts/cfplib/preflight.py:218, 238 | `manual` names both the unevaluated rule list and `kind: manual` on model-added findings | Store `kind: added` for `add_finding` entries; rename the list to `unevaluated` in output and contract | ambiguous (contract rename) |
| M8 | cfp/scripts/cfp_store.py:237-248 | `preflight --proposal X add-finding ...` also parses; the parent `--proposal` and the subcommand share a name | Make `preflight run` an explicit subcommand or document the shape | ambiguous |
| M9 | cfp/scripts/cfplib/frontmatter.py (`_dump_map`, `build_body`) | Keys with newlines write unparseable files; section text containing a `## ` line splits the section on reload | Validate keys against `^[A-Za-z0-9_][A-Za-z0-9_.-]*$`; reject or escape `## ` lines in section text | unambiguous |
| M10 | cfp/scripts/cfplib/talks.py:49-54 (also bios.py:100, profile.py:415) | Slug collision check is case-sensitive; on APFS `Foo.md` is clobbered by title "Foo" | Compare lowercased stems and check `path.exists()` before treating the write as a create | unambiguous |
| M11 | cfp/scripts/cfplib/frontmatter.py:141-146 | Folded `>` scalars lose paragraph breaks and are rewritten as `|` | Join lines within a paragraph with a space and keep one newline per blank line | unambiguous |
| M12 | cfp/scripts/test/test_lifecycle.py:80-88 | US4-S3 negative half untested: rejected and withdrawn must leave talk outings untouched | Assert `outings == []` after both transitions; add a preflight test where the only history is a rejected proposal | unambiguous |
| M13 | cfp/scripts/test (various) | Error paths untested: invalid `--date`, non-integer `config set`, bare `preflight`, non-list co_speakers, bool review scores, criterion exactly at `pass_min_criterion` | Add the six small tests named by the test agent | unambiguous |
| M14 | cfp/scripts/test/test_preflight.py:106-179 | `source` not asserted for track, speaker-count, all-men, multi-company findings; `shift_months` clamping, empty tracks, and future outings untested | Add a shared `source` assertion and three small tests | unambiguous |
| M15 | cfp/scripts/test/test_frontmatter.py | No non-ASCII round-trip test (umlaut, emoji) through parser and CLI | Add `test_round_trip_non_ascii` and a CLI case with `--speaker-name "Roland Huß"` | unambiguous |
| M16 | cfp/scripts/test/test_cli_foundation.py:155-161 | US3-S3 "family profile unchanged" half not asserted after `event write` | Capture `profile.md` bytes before and assert identical after | unambiguous |
| M17 | cfp/scripts/cfplib/frontmatter.py:57-63 | `a: [x # y, z]` now yields the string `[x` instead of a list (was non-standard before; dumper never emits it) | Strip comments only after the closing bracket for flow sequences, or reject the form | unambiguous |

## Notable Observations

Captured to brainstorm/idea-inbox.md.

### NOTABLE-1
- **File:** cfp/scripts/cfplib/preflight.py (repeat rule)
- **Category:** correctness
- **Source:** correctness-agent
- **Description:** The repeat rule downgrades to warn whenever `previously_presented` is non-empty, and the draft skill always fills that field, so for KubeCon the rule can never disqualify a completed proposal.
- **Rationale:** Matches FR-030 literally, but "the note exists" and "the note explains significant differences" are different things; a confirmation question or a minimum-length heuristic may be worth a spec clarification.

### NOTABLE-2
- **File:** cfp/scripts/cfplib/config.py:20, proposals.py:33
- **Category:** architecture
- **Source:** architecture-agent
- **Description:** `review_rounds` names both the integer round limit in config.md and the list of recorded rounds on a proposal.
- **Rationale:** Same key, two types, both read in the same draft step; a future contract revision could rename the config key to `max_review_rounds`.

### NOTABLE-3
- **File:** cfp/skills/*/SKILL.md:2
- **Category:** architecture
- **Source:** architecture-agent
- **Description:** Skill frontmatter uses `name: cfp:<dir>` while the agent file uses the bare `committee-reviewer`; validation passes today.
- **Rationale:** If the loader enforces the documented character set, all seven skills stop loading at once.

### NOTABLE-4
- **File:** cfp/scripts/cfplib/pasteview.py:42
- **Category:** architecture
- **Source:** architecture-agent
- **Description:** The JSON paste view emits a `kind` per field that nothing consumes.
- **Rationale:** Either drop it or use it to skip the count line for choice and boolean fields.

### NOTABLE-5
- **File:** cfp/scripts/cfplib/profile.py (write_profile_from_json)
- **Category:** security
- **Source:** security-agent
- **Description:** A family profile rewrite keeps `approved: true` from the existing file, unlike event overrides which reset to false.
- **Rationale:** FR-010 asks before changing the family profile, but the gate lives only in skill prose; mirroring the event behavior would back it in the script.

### NOTABLE-6
- **File:** cfp/hooks.json
- **Category:** production-readiness
- **Source:** production-agent
- **Description:** The hook launches python3 on every prompt; a missing interpreter surfaces a shell error everywhere. A 5 second timeout was added; the interpreter guard was not.
- **Rationale:** Wrapping the command in `command -v python3 && ... || true` keeps non-cfp sessions silent.

### NOTABLE-7
- **File:** cfp/scripts/cfplib/config.py (init_store)
- **Category:** production-readiness
- **Source:** production-agent
- **Description:** A seed profile is never refreshed once present; `seed_version` is stored but never compared.
- **Rationale:** Plugin updates that correct limits or add event files reach only new stores.

### NOTABLE-8
- **File:** cfp/scripts/cfplib/store.py:18-25
- **Category:** production-readiness
- **Source:** production-agent
- **Description:** Non-Latin titles slugify to `item`, `item-2`, and so on.
- **Rationale:** The draft skill could propose an ASCII id when the slug degenerates, or fall back to a short hash.

### NOTABLE-9
- **File:** cfp/scripts/cfplib/preflight.py (run)
- **Category:** test-quality
- **Source:** test-agent
- **Description:** A pre-flight re-run discards manual findings such as the audience-level warning; no test pins this either way.
- **Rationale:** The check and draft skills re-add the finding after each run, so the behavior is consistent, but it should be stated in a test.

### NOTABLE-10
- **File:** cfp/scripts/test/conftest.py:23-37
- **Category:** test-quality
- **Source:** test-agent
- **Description:** HOME isolation is an opt-in fixture; a future test calling `init_store` without it would write the real user config.
- **Rationale:** An autouse fixture would make the isolation structural.

### NOTABLE-11
- **File:** cfp/scripts/cfplib/proposals.py (demote_ready)
- **Category:** correctness
- **Source:** round-2 re-review agent
- **Description:** A draft with a passing review can be edited and then set ready after a clean pre-flight without a new review; this is intentional for the voice pass and shortening steps, and the docstring now says so.
- **Rationale:** If a stricter model is wanted, `mark-voice-pass` could become the only sanctioned post-pass edit path.

## Goal Alignment

Skipped: no PR and no git remote exist for this branch.

## Post-Fix Spec Coverage

The fix loop removed code (a duplicated date helper, an unused path helper, a no-op block in `init_store`, and the private proposal loader in lifecycle). None of these carried a requirement on its own. Coverage after the loop:

| Requirement group | Implementation | Status |
|---|---|---|
| FR-001 to FR-003 store and config | cfplib/config.py, store.py, frontmatter.py (body preserved, atomic saves) | verified |
| FR-004 to FR-010a profiles | cfplib/profile.py (effective merge now carries the event limit), skills/profile | verified |
| FR-011, FR-012 talks | cfplib/talks.py, skills/draft Steps 3 and 4 | verified |
| FR-013 to FR-023 drafting | skills/draft, cfplib/proposals.py, review.py, pasteview.py, counts.py | verified |
| FR-024 to FR-027 bios and resources | cfplib/bios.py, skills/bio (Write tool added) | verified |
| FR-028 to FR-030 pre-flight | cfplib/preflight.py (all_men and submission_limit corrected), skills/check | verified |
| FR-031 to FR-035 lifecycle | cfplib/lifecycle.py (new transitions, stale checks), skills/status (profile column) | verified |
| FR-036 to FR-038 out of scope | no submission, co-speaker bio, or slide code exists | verified |

All spec requirements verified after the fix loop.

## Test Suite Results

| Round | Test Command | Exit Code | Failures | Status |
|-------|-------------|-----------|----------|--------|
| 1 | make test | 0 | 0 | passed (146 tests after the round's additions) |
| 2 | make test | 0 | 0 | passed (148) |
| 3 | make test | 0 | 0 | passed (149) |

`make lint-dashes`, `make validate`, and `make test-hook` passed after every round. Test suite passed in all fix rounds.

## Remaining Findings

No Critical or Important findings remain. The 17 Minor and 11 Notable items above are advisory.
