# Guided Demo Report

**Feature**: CFP and Bio Plugin for Conference Submissions
**Date**: 2026-10-09
**Spec**: specs/001-cfp-plugin/spec.md
**Result**: 6 passed, 0 skipped, 0 failed, 1 manual (out of 7)

---

## Triage Summary

| Tier | Count | Detail |
|------|-------|--------|
| full | 5 | CLI flows run against a scratch store with python3 |
| partial | 1 | Reviewer agent prompt run through a general-purpose subagent, not the installed plugin dispatch |
| setup_offered | 0 | |
| manual | 1 | Interactive skills need the plugin installed in a fresh Claude Code session |

User selection: Run everything possible.

Demo store: a scratch directory under the session scratchpad, created with `config init` and the plugin's seed directory. No application process was started.

---

## Flow 1: Init a store and inspect the seeded KubeCon profile

**Tier**: full
**Covers**: FR-001, FR-002, FR-002a, FR-004, FR-005, FR-006, FR-009

### Setup
Fresh scratch directory, `CFP_STORE` pointed at it.

### Evidence
**Execution**: `config init --store <scratch> --speaker-name "Roland Huss" --speaker-company "Red Hat" --voice-profile blog --review-rounds 3 --seed-dir cfp/knowledge-base/profiles`, then `profile list`, `profile show --profile kubecon --event kubecon-eu-2027`, `profile validate`.
**Output**:
```
seeded_profiles: ["kubecon"]
config.md: speaker_name, speaker_company, voice_profile, review_rounds, default_profile
profile list: kubecon approved, seed_version 2026-10-09, events kubecon-eu-2027 (13 tracks, days_to_close 2) and kubecon-na-2026 (11 tracks)
profile show: submission_limit 3, bio_limit 500 unverified, tutorial 80 min 1 to 5 speakers,
  fields title 75 / abstract 1300 / benefits 1000 all unverified, benefits reviewer-only,
  rubric content, originality, relevance, speaker, not_product_pitch, pass 4.0 average and 3.0 minimum
profile validate: valid true, problems []
```

### Verdict: PASS

**Verify yourself**:
1. `CFP_STORE=$(mktemp -d)/s python3 -I cfp/scripts/cfp_store.py config init --store "$CFP_STORE" --speaker-name T --seed-dir cfp/knowledge-base/profiles`
2. `python3 -I cfp/scripts/cfp_store.py profile show --profile kubecon --event kubecon-eu-2027 --store "$CFP_STORE"` and look for 13 tracks and `duration_min: 80` on the tutorial.

---

## Flow 2: Create bio variations and a speaker resource

**Tier**: full
**Covers**: FR-024, FR-025

### Evidence
**Execution**: `bio write --name short-cloud-native --emphasis cloud-native --target-length 450 --text-file ...`, `bio write --name long-ai ... --target-length 800`, `resource write --from-json ...` (type recording), `bio list`, `resource list`.
**Output**:
```
bio list: long-ai (ai, 800, 761 chars), short-cloud-native (cloud-native, 450, 325 chars)
resource list: kubecon-eu-2025-session-recording (recording, link, date 2025-04-02)
bios/short-cloud-native.md: front matter with chars: 325, body is the third-person text
```

### Verdict: PASS

**Verify yourself**: `python3 -I cfp/scripts/cfp_store.py bio list --store <scratch>` and open a bio file in any editor.

---

## Flow 3: Build a talk and a proposal, fill fields, count, paste view

**Tier**: full
**Covers**: FR-011, FR-016, FR-022, FR-023, FR-026, FR-027

### Evidence
**Execution**: `talk write --from-json` (all five story sections, personas, projects, resource link), `talk complete`, `proposal create --talk ... --profile kubecon --event kubecon-eu-2027 --session-type session --angle problem-first`, `proposal set-meta --from-json` (track, Intermediate, bio long-ai, resource), `count`, eleven `proposal set-field` calls, `proposal set-bio-text` with the short bio, `count`, `pasteview --format markdown`.
**Output**:
```
talk id: what-broke-when-we-put-coding-agents-on-a-shared-kubernetes (slug cut at 60 chars by design)
talk complete: complete true
set-meta with bio long-ai, then count: bio 761/500 status over
set-field title 68/75, abstract 973/1300, benefits 781/1000, all unverified; choice fields no-limit
set-bio-text short: 325/500; bios/long-ai.md still chars: 761
count: over [], missing_required []
pasteview: 11 fields in form order with counts and limits, unverified-limit warning, bio last
```

### Verdict: PASS

Reviewer note: the 60 character slug limit truncated the talk id, which is the documented rule but worth knowing when scripting against ids.

**Verify yourself**: `python3 -I cfp/scripts/cfp_store.py pasteview --proposal <id> --format markdown --store <scratch>`.

---

## Flow 4: Committee review packet and recorded verdict

**Tier**: partial
**Covers**: FR-018, FR-020

### Setup
`review packet --proposal <id> --examples 3` written to a file. A general-purpose subagent was given the plugin's agent definition `cfp/agents/committee-reviewer.md` and the packet, and told to follow the definition only.

### Evidence
**Execution**: subagent run, then `review record --from-json <reviewer output>`, `review history`, `status ready-check`, and `review record` with a JSON missing a criterion.
**Output**:
```
packet: rubric with 5 criteria, thresholds 4.0 / 3.0, 8 rejection reasons, 1 calibration example (official LF sample), 11 fields, bio, level, track
reviewer JSON: scores content 4.5, originality 4.0, relevance 4.5, speaker 4.0, not_product_pitch 4.5;
  comments cite the placeholder recording link, the unnamed rolled-back guardrails, the vague third takeaway;
  5 suggestions tagged resources, open_source_projects, abstract, benefits, abstract; verdict pass
review record: round 1, verdict pass, average 4.3, below_min []
review history: round 1 persisted with scores and date
ready-check: can_ready false, reason: pre-flight disqualifying findings (demo store has 3 submitted proposals for the event)
malformed JSON: error "reviewer JSON is missing a comment for criterion 'content'"
```

**Partial evidence disclaimer**: the reviewer prompt was executed by a subagent reading the agent file, not by the installed plugin's `cfp:committee-reviewer` dispatch. This proves the prompt yields usable, specific scoring and the record path works; it does not prove the agent name resolves after `make install`.

### Verdict: PASS

**Verify yourself**: after install, run step 3 of Flow 7 and look at the review table.

---

## Flow 5: Pre-flight hard rules on violating proposals

**Tier**: full
**Covers**: FR-028, FR-028a, FR-030

### Evidence
**Execution**: three filler proposals for kubecon-eu-2027 set to submitted, `preflight` on a fourth; a proposal with track "Serverless Wonderland"; a talk with a presented outing at KubeCon EU 2026 (2026-03-25) proposed for kubecon-na-2026, before and after filling the previously-presented note; `preflight add-finding` with an audience-level warning.
**Output**:
```
submission-limit: disqualify, "3 proposals already count toward the limit of 3 ...", source LF CFP URL
track-in-event: disqualify, lists the 13 event tracks
repeat-one-year: disqualify; after the note is filled: warn
add-finding: audience-level warn stored, passed true
manual: ["vendor-pitch"]
```

### Verdict: PASS

**Verify yourself**: `python3 -I cfp/scripts/cfp_store.py preflight --proposal <id> --today 2026-10-09 --store <scratch>`.

---

## Flow 6: Lifecycle transitions and side effects

**Tier**: full
**Covers**: FR-031, FR-031a, FR-032, FR-033, FR-034, FR-035

### Evidence
**Execution**: `status set` to accepted (2026-12-07) and presented (2027-03-16) on one filler proposal; to rejected on another, then `proposal create` for the same talk against kubecon-na-2026; `status set --to presented` on the rejected one; `proposal list`; `status ready-check` on the unreviewed main proposal.
**Output**:
```
accepted: side_effects ["added calibration example profiles/kubecon/examples/kubecon-eu-2027--filler-talk-2.md"]
presented: side_effects ["recorded presented outing on talk filler-talk-2 (kubecon-eu-2027, 2027-03-16)"]; talk file shows the outing
rejected: decided_on 2026-12-07; proposal create for kubecon-na-2026 succeeded
rejected to presented: error "allowed targets: none"
proposal list: statuses draft, submitted, presented, rejected with their dates
ready-check: can_ready false with both reasons named
```

### Verdict: PASS

**Verify yourself**: `ls <scratch>/profiles/kubecon/examples/` after marking a proposal accepted.

---

## Flow 7: Interactive commands in a live session

**Tier**: manual
**Covers**: FR-007, FR-008, FR-010, FR-010a, FR-013, FR-015, FR-017, FR-021, FR-021a, FR-029

### Verdict: MANUAL

The plugin was not installed in the demo session and these flows are conversation-driven, so running them here would be simulation. Steps for a later session:

1. In the repository root run `make install`, then start a fresh Claude Code session in any directory.
2. `/cfp:init` and point the store at a scratch folder.
3. `/cfp:draft`, choose kubecon and kubecon-eu-2027, session type session, input "one-line idea", answer the interview. Expect two or three angles, every field drafted, a five-criterion review table with a verdict, the voice pass or its skip notice, pre-flight, and the paste view. Confirm the proposal file ends in status ready.
4. `/cfp:profile refresh kubecon --event kubecon-eu-2027 --screenshots <path to a Sessionize form screenshot>`. Expect screenshot fields with `limit_status: screenshot` and the family profile unchanged unless approved.
5. `/cfp:draft --profile kubecon --event kubecon-india-2026`. Expect the inline override offer instead of a block.
6. `/cfp:check <proposal>` on a proposal labeled Beginner with an advanced abstract. Expect an audience-level warning.
7. Open the scratch store in Obsidian, edit a bio there, then `/cfp:bio list`. Expect the new count (SC-008).

---

## FR Coverage

| FR | Flow | Verdict | Classification |
|----|------|---------|----------------|
| FR-001 | Flow 1 | PASS | observable |
| FR-002 | Flow 1 | PASS | observable |
| FR-002a | Flow 1 | PASS | observable |
| FR-003 | - | - | internal-only (hand-edit tolerance, unit tests) |
| FR-004 | Flow 1 | PASS | observable |
| FR-005 | Flow 1 | PASS | observable |
| FR-006 | Flow 1 | PASS | observable |
| FR-007 | Flow 7 | MANUAL | observable |
| FR-008 | Flow 7 | MANUAL | observable |
| FR-009 | Flow 1 | PASS | observable |
| FR-010 | Flow 7 | MANUAL | observable |
| FR-010a | Flow 7 | MANUAL | observable |
| FR-011 | Flow 3 | PASS | observable |
| FR-012 | - | - | internal-only (input source selection, skill text) |
| FR-013 | Flow 7 | MANUAL | observable |
| FR-014 | - | - | internal-only (session type refusal logic, skill text) |
| FR-015 | Flow 7 | MANUAL | observable |
| FR-016 | Flow 3 | PASS | observable |
| FR-017 | Flow 7 | MANUAL | observable |
| FR-018 | Flow 4 | PASS | observable |
| FR-019 | - | - | internal-only (scoring semantics, agent text) |
| FR-020 | Flow 4 | PASS | observable |
| FR-021 | Flow 7 | MANUAL | observable |
| FR-021a | Flow 7 | MANUAL | observable |
| FR-022 | Flow 3 | PASS | observable |
| FR-023 | Flow 3 | PASS | observable |
| FR-024 | Flow 2 | PASS | observable |
| FR-025 | Flow 2 | PASS | observable |
| FR-026 | Flow 3 | PASS | observable |
| FR-027 | Flow 3 | PASS | observable |
| FR-028 | Flow 5 | PASS | observable |
| FR-028a | Flow 5 | PASS | observable |
| FR-029 | Flow 7 | MANUAL | observable |
| FR-030 | Flow 5 | PASS | observable |
| FR-031 | Flow 6 | PASS | observable |
| FR-031a | Flow 6 | PASS | observable |
| FR-032 | Flow 6 | PASS | observable |
| FR-033 | Flow 6 | PASS | observable |
| FR-034 | Flow 6 | PASS | observable |
| FR-035 | Flow 6 | PASS | observable |
| FR-036 | - | - | internal-only (MUST NOT) |
| FR-037 | - | - | internal-only (MUST NOT) |
| FR-038 | - | - | internal-only (MUST NOT) |

## Internal-Only FRs

Verified by unit tests or by reading the skill and agent text, no user-observable demo:

- **FR-003**: tolerate hand edits that keep front matter valid (keyword: constraint)
- **FR-012**: four input sources for a talk (keyword: default, model-driven selection)
- **FR-014**: refuse session types the solo speaker cannot satisfy (keyword: MUST, refusal logic)
- **FR-019**: rejection reasons and examples lower scores (keyword: internal scoring semantics)
- **FR-036**: no auto-submission (keyword: MUST NOT)
- **FR-037**: no co-speaker bio management (keyword: MUST NOT)
- **FR-038**: no slides or post-acceptance material (keyword: MUST NOT)
