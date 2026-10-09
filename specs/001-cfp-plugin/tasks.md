---

description: "Task list for the CFP and Bio plugin"
---

# Tasks: CFP and Bio Plugin for Conference Submissions

**Input**: Design documents from `/specs/001-cfp-plugin/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/commands.md, contracts/scripts.md, contracts/store-files.md, quickstart.md

**Tests**: The plan (research.md R9) defines pytest coverage for every `cfplib` module. Test tasks are included for the deterministic Python code and are written before the module they cover. Skill and command behavior is validated through the quickstart scenarios, not unit tests.

**Organization**: Tasks are grouped by user story. The Python library and CLI subcommands that more than one story needs live in the Foundational phase so each story phase stays independently testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story label (US1 to US5) for story phase tasks
- Every task names exact file paths relative to the repository root

## Path Conventions

Plugin source lives under `cfp/` (nested layout, see plan.md). Scripts under `cfp/scripts/`, library under `cfp/scripts/cfplib/`, tests under `cfp/scripts/test/`, skills under `cfp/skills/<name>/SKILL.md`, commands under `cfp/commands/<name>.md`, knowledge base under `cfp/knowledge-base/`.

Conventions that apply to every task: no em-dash or en-dash characters in any markdown or string the user will read; Python is standard library only and must run with `python3 -I`; every CLI subcommand prints one JSON object (see contracts/scripts.md); commit after each task or logical group with the `Assisted-By: 🤖 Claude Code` trailer.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Repository scaffolding, manifests, hook, and developer tooling

- [x] T001 Create the plugin directory tree from plan.md: `cfp/.claude-plugin/`, `cfp/commands/`, `cfp/skills/`, `cfp/agents/`, `cfp/knowledge-base/profiles/kubecon/events/`, `cfp/knowledge-base/profiles/kubecon/examples/`, `cfp/knowledge-base/templates/`, `cfp/knowledge-base/guidance/`, `cfp/hooks/scripts/`, `cfp/scripts/cfplib/`, `cfp/scripts/test/`, plus root `.claude-plugin/`
- [x] T002 [P] Write `.claude-plugin/marketplace.json` (name `cc-cfp-marketplace`, plugin `cfp`, source `./cfp`, owner Roland Huss, license Apache-2.0) and `cfp/.claude-plugin/plugin.json` (name `cfp`, version 0.1.0, description, keywords cfp, conference, speaker, kubecon, `hooks: ./hooks.json`)
- [x] T003 [P] Write `cfp/hooks.json` registering a UserPromptSubmit hook that runs `python3 -I ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/context-hook.py`
- [x] T004 [P] Write `cfp/hooks/scripts/context-hook.py`: read stdin JSON, exit silently unless the prompt starts with `/cfp:`, resolve plugin root from the script location, read `~/.config/cc-cfp/config.json` (or env `CFP_STORE`) to find the store, emit `additionalContext` with `<cfp-context>` containing `plugin-root`, `store`, `store-initialized` (true when `<store>/config.md` exists), and `today` (ISO date), per contracts/commands.md; a missing or malformed `config.json` yields an empty `store` and `store-initialized` false, and the hook never exits non-zero for a `/cfp:` prompt
- [x] T005 [P] Write `Makefile` with targets `validate` (claude plugin validate on `./` and `./cfp/`), `install`, `uninstall`, `reinstall`, `test` (`~/.venvs/cc-cfp/bin/python -m pytest cfp/scripts/test -q`), `test-hook` (pipe a `/cfp:status` prompt JSON through the hook and grep for `cfp-context`), `lint-dashes` (fail when `rg` finds em-dash or en-dash in `cfp/` or `README.md`), `clean`, `help`
- [x] T006 [P] Write `.gitignore` (Python caches, `.claude/settings.local.json`, `.claude/worktrees/`, `.DS_Store`, `*.log`) and `cfp/requirements-dev.txt` containing `pytest`
- [x] T007 [P] Write `cfp/scripts/test/conftest.py` with fixtures: `tmp_store` (temporary directory, sets env `CFP_STORE`), `seeded_store` (runs the `config init` code path with `--seed-dir cfp/knowledge-base/profiles`), and `run_cli` (invokes `cfp_store.py` in a subprocess with `python3 -I` and parses JSON stdout)

**Checkpoint**: `make validate` passes on the manifests, `make test-hook` prints a `<cfp-context>` block, `uv venv ~/.venvs/cc-cfp && uv pip install --python ~/.venvs/cc-cfp/bin/python -r cfp/requirements-dev.txt` prepares the test environment.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Store library, CLI skeleton, seed profile, templates, and the init flow every command depends on

**CRITICAL**: No user story work can begin until this phase is complete

### Library and CLI

- [x] T008 [P] Write `cfp/scripts/test/test_frontmatter.py` covering: parse scalars (string, int, float, bool, ISO date), flat lists, list of flat maps, one nested map, `|` block scalars; unquoted scalars containing `: ` or `#` inside URLs and track names (for example `Platform Engineering: DevEx & IDPs`, `https://events.linuxfoundation.org/...`), double-quoted strings, and empty values (`submitted_on:`) parsing as null and round-tripping as empty; round-trip write preserves unknown keys and key order; body sections split by `## ` headings; parse error reports file path and line number
- [x] T009 Implement `cfp/scripts/cfplib/frontmatter.py`: `parse(text) -> (meta, body)`, `dump(meta, body) -> text`, `sections(body) -> ordered dict of heading to text`, `set_section(body, heading, text)`, `FrontmatterError(path, line, message)`; stdlib only, subset defined in research.md R3
- [x] T010 [P] Write `cfp/scripts/test/test_config.py` covering: store resolution order (`--store`, env `CFP_STORE`, user config file at a patched home), `config init` creates the folder tree and `config.md` and writes the user config, `config set` updates one key, missing store raises a clear error
- [x] T011 Implement `cfp/scripts/cfplib/config.py`: `resolve_store(cli_store)`, `load_user_config()`, `write_user_config(store)`, `load_store_config(store)`, `write_store_config(store, values)`, `init_store(store, values, seed_dir)` (creates `profiles/`, `talks/`, `proposals/`, `bios/`, `resources/`, copies each seed profile directory not already present and sets `approved: true` plus `seed_version` from the seed's own value)
- [x] T012 [P] Write `cfp/scripts/test/test_store.py` covering: slug generation rules (lowercase ASCII, hyphens, max 60 chars, `-2` collision suffix), path helpers for every entity type, `list_entities` skipping files with invalid front matter while reporting them, load and save of a talk, bio, resource, proposal
- [x] T013 Implement `cfp/scripts/cfplib/store.py`: `slugify(text, existing)`, path helpers (`talk_path`, `proposal_path`, `bio_path`, `resource_path`, `profile_path`, `event_path`, `example_path`), generic `load(path)`, `save(path, meta, body)`, `list_dir(kind) -> (items, problems)` where problems carry path and parse error text
- [x] T014 [P] Write `cfp/scripts/test/test_profile.py` covering: effective event merge (submission_limit override, session type replace and remove, field override by id), validation problems (duplicate field ids, unknown rule kind, empty rubric on approved profile), approval checks for profile and event, calibration example add and list newest first with limit
- [x] T015 Implement `cfp/scripts/cfplib/profile.py`: `load_profile(store, id)`, `load_event(store, profile_id, event_id)`, `effective(profile, event)`, `validate(profile, event)`, `approve(...)`, `write_profile_from_json`, `write_event_from_json`, `add_example`, `list_examples`, `days_to_close(event, today)`
- [x] T016 [P] Write `cfp/scripts/test/test_lifecycle.py` covering every allowed transition in the data-model state machine, rejection of disallowed transitions with the list of allowed targets, date fields set per transition, `accepted` creating a calibration example from the proposal fields, `presented` appending a `presented` outing to the talk, `ready` refused without a pass verdict or failing pre-flight unless forced, submission counting by status set; the tests write proposal and talk files directly from `cfp/knowledge-base/templates/` because `proposal create` arrives later in T034
- [x] T017 Implement `cfp/scripts/cfplib/lifecycle.py`: `TRANSITIONS` table, `set_status(store, proposal_id, to, date, force)`, `ready_check(store, proposal_id)`, `count_submissions(store, event_id, exclude_proposal)`, side effects for accepted and presented
- [x] T018 [P] Write `cfp/scripts/test/test_bio_resource.py` covering: bio write recounts `chars` from body text, list and show, delete, resource write generates id from title, resource list filtered by type
- [x] T019 Implement bio and resource helpers in `cfp/scripts/cfplib/bios.py` (using the generic load, save, and list helpers from `store.py`): `write_bio`, `list_bios`, `show_bio`, `delete_bio`, `write_resource`, `list_resources`, `delete_resource`
- [x] T020 Implement `cfp/scripts/cfp_store.py` CLI skeleton with argparse subcommand groups and JSON output conventions from contracts/scripts.md (`ok`, `error`, exit codes 0, 1, 2; `--store`, `--today` globals), wiring these subcommands: `config show|init|set`, `profile list|show|validate|write|approve`, `event write|list`, `example add|list`, `bio list|show|write|delete`, `resource list|write|delete`, `status set|ready-check`; every `list` subcommand (here and in T032, T034) adds a `problems: [{path, error}]` key naming files skipped for invalid front matter (spec edge case, mirror this in contracts/scripts.md); add `cfp/scripts/test/test_cli_foundation.py` that runs each wired subcommand through `run_cli` against `seeded_store`

### Knowledge base and seed profile

- [x] T021 [P] Write front matter templates in `cfp/knowledge-base/templates/`: `talk.md`, `proposal.md`, `bio.md`, `resource.md`, `profile.md`, `event.md`, `example.md`, each matching contracts/store-files.md with placeholder values and the required body headings
- [x] T022 [P] Write the seed profile `cfp/knowledge-base/profiles/kubecon/profile.md` from brainstorm/research/kubecon-cfp-research.md: five session types (session, panel, lightning, tutorial, poster) with durations and speaker limits, `submission_limit: 3`, ordered fields (title 75, abstract 1300, benefits 1000 reviewer-only, case_study boolean, previously_presented longtext, cncf_projects text (guidance: comma-separated CNCF project names as listed on the form), open_source_projects text, resources resources, audience_level choice Any/Beginner/Intermediate/Advanced, track choice filled from the event, format choice) all with `limit_status: unverified` and guidance text, the five-criterion rubric (content, originality, relevance, speaker, not_product_pitch) with `scale_max: 5`, `pass_average: 4.0`, `pass_min_criterion: 3.0`, rules (submission-limit disqualify, repeat-one-year warn-when-noted, track-in-event disqualify, speaker-count disqualify, all-men-panel disqualify, multi-company-panel disqualify, vendor-pitch manual) each with its source URL, `rejection_reasons` from section 9e, `bio_limit: 500` unverified, `approved: true`, `seed_version: "2026-10-09"`, and a `## Drafting guidance` section summarizing sections 9c and 9d (first two sentences carry the value, explicit takeaways, hard parts and lessons, third person, no bullet lists in the abstract)
- [x] T023 [P] Write seed event overrides `cfp/knowledge-base/profiles/kubecon/events/kubecon-eu-2027.md` (Barcelona, 15 to 18 Mar 2027, CFP 10 Aug to 11 Oct 2026, notify 7 Dec 2026, 13 tracks, tutorial 80 min, `approved: true`) and `cfp/knowledge-base/profiles/kubecon/events/kubecon-na-2026.md` (Salt Lake City, 9 to 12 Nov 2026, CFP 6 Apr to 31 May 2026, notify 3 Aug 2026, 11 tracks, tutorial 75 min, `approved: true`) with source URLs
- [x] T024 [P] Write `cfp/knowledge-base/profiles/kubecon/examples/lf-sample-container-runtime.md` holding the Linux Foundation sample submission ("OCI, CRI, ??: Making Sense of the Container Runtime Landscape in Kubernetes") with its Benefits text summarized from the research, `origin: official-sample`, and a `## Why it worked` note
- [x] T025 [P] Write `cfp/knowledge-base/guidance/abstract-angles.md`: how to derive problem-first, story-driven, and contrarian angles from a talk story, what makes a title specific, the two-sentence value rule, how to present candidates for selection
- [x] T026 [P] Write `cfp/knowledge-base/guidance/benefits-field.md`: structure for a reviewer-only relevance field (who benefits by persona, why now, what is new versus prior talks, evidence and credentials, data or case study shown), with the rule that it must not restate the abstract and examples of good and bad openings
- [x] T027 [P] Write `cfp/knowledge-base/guidance/profile-research.md`: checklist of what to extract from CFP pages, reviewer guideline pages, and form screenshots (session types, field labels and order, required markers, limits, option lists, tracks, dates, rules, rubric), how to mark verification status and sources, and how to present a draft per section for approval

### Init flow

- [x] T028 Write `cfp/skills/init/SKILL.md`: Step 0 reads `<cfp-context>`; asks store path (default `~/Obsidian/<vault>/Talks` when `~/Obsidian/*` exists, else `~/cfp-store`), speaker name, company, voice profile (lists `~/.claude/style/voices/*.yaml` and `.style/voices/*.yaml` when present, allows none), review rounds; runs `config init --seed-dir "$PLUGIN_ROOT/knowledge-base/profiles"`; reports seeded profiles and next command; one question at a time via AskUserQuestion; `allowed-tools` Bash, Read, AskUserQuestion, Glob
- [x] T029 [P] Write `cfp/commands/init.md` (frontmatter description and argument-hint `[--store <path>]`) delegating to the `cfp:init` skill with `$ARGUMENTS`
- [x] T030 Write `cfp/skills/_shared/preamble.md` (included by reference from every skill) describing Step 0: parse `<cfp-context>`, offer `/cfp:init` when `store-initialized` is false, the shared interaction rules from contracts/commands.md, and the exact CLI invocation pattern `python3 -I "$PLUGIN_ROOT/scripts/cfp_store.py"`

**Checkpoint**: `make test` passes for all foundation modules; `python3 -I cfp/scripts/cfp_store.py config init --store /tmp/x --speaker-name T --seed-dir cfp/knowledge-base/profiles` seeds `kubecon` with two events; `profile show --profile kubecon --event kubecon-eu-2027` returns 13 tracks and an 80 minute tutorial; `profile validate` reports no problems.

---

## Phase 3: User Story 1 - Draft a KubeCon proposal from an idea (Priority: P1) MVP

**Goal**: Interactive drafting from a one-line idea to a reviewed, voiced, pre-flight-checked proposal with a paste view

**Independent Test**: With a freshly initialized store, `/cfp:draft` with a one-line idea ends with `proposals/kubecon-eu-2027--<talk>.md` in status `ready`, every required field present and under its limit, at least one review round with five scored criteria, and a printed paste view (quickstart Scenario 1)

### Library and CLI for drafting

- [x] T031 [P] [US1] Write `cfp/scripts/test/test_talk.py` covering: `talk write` creates with slug from title, updates `updated`, sections written and read back, `talk complete` lists empty sections, `talk list` includes proposal ids and last presented date
- [x] T032 [US1] Implement talk operations in `cfp/scripts/cfplib/talks.py` (`write_talk`, `show_talk`, `list_talks`, `complete_talk`) and wire `talk list|show|write|complete` in `cfp/scripts/cfp_store.py`
- [x] T033 [P] [US1] Write `cfp/scripts/test/test_proposal.py` covering: `proposal create` refuses duplicate talk and event, unapproved profile or event, unknown session type; `set-field` writes the `## Field:` section and returns count status (`ok`, `over`, `unverified`, `no-limit`); unknown field id error; `set-meta` updates keys and `--bio` copies the snapshot into `## Bio`; `set-bio-text` replaces only the snapshot; `mark-voice-pass`
- [x] T034 [US1] Implement proposal operations in `cfp/scripts/cfplib/proposals.py` (`create`, `show`, `list`, `set_field`, `set_meta`, `set_bio_text`, `mark_voice_pass`) and wire `proposal create|show|list|set-field|set-meta|set-bio-text|mark-voice-pass` in `cfp/scripts/cfp_store.py`
- [x] T035 [P] [US1] Write `cfp/scripts/test/test_counts.py` covering: character counting of field text (leading and trailing whitespace trimmed, CRLF normalized to LF before counting, Unicode code points counted so `ß` and an emoji each count as 1), limit status per field, empty text counts 0 and lands in `missing_required` for a required field, `over` and `missing_required` lists, bio counted against `bio_limit`
- [x] T036 [US1] Implement `cfp/scripts/cfplib/counts.py` (`count_proposal(store, proposal_id) -> dict`) and wire `count` in `cfp/scripts/cfp_store.py`
- [x] T037 [P] [US1] Write `cfp/scripts/test/test_pasteview.py` covering: fields in effective form order, drafted text, `chars/limit` display, `OVER LIMIT` and `limit unverified` flags, choice fields shown as single values, bio appended last, JSON and markdown formats
- [x] T038 [US1] Implement `cfp/scripts/cfplib/pasteview.py` (`render(store, proposal_id, fmt)`) and wire `pasteview` in `cfp/scripts/cfp_store.py` (markdown goes to stdout verbatim when `--format markdown`)
- [x] T039 [P] [US1] Write `cfp/scripts/test/test_review.py` covering: `review packet` includes rubric, thresholds, rejection reasons, up to n examples, drafted fields, level, track, session type; `review record` rejects JSON missing a criterion, appends a round, computes verdict from average and minimum (reviewer verdict advisory), returns suggestions; `review history`
- [x] T040 [US1] Implement `cfp/scripts/cfplib/review.py` (`packet`, `record`, `history`) and wire `review packet|record|history` in `cfp/scripts/cfp_store.py`
- [x] T041 [P] [US1] Write `cfp/scripts/test/test_preflight.py` covering each rule kind one at a time per contracts/scripts.md: submission_limit (count by status, excluding self), repeat_within_months (presented outing within window, boundary pinned: an outing dated exactly `params.months` months before `--today` is inside the window and one day earlier is outside; outings of kind `submitted` or of another family ignored; downgraded to warn when the previously-presented field is non-empty), track_in_event (case-insensitive), speaker_count, all_men_panel (disqualify when all known genders are man, warn when unknown), multi_company_panel, vendor_pitch and custom listed under `manual`; result stored in the proposal's `preflight` map; `ok` false only on disqualify
- [x] T042 [US1] Implement `cfp/scripts/cfplib/preflight.py` (`run(store, proposal_id, today)`, `add_finding(...)`) and wire `preflight` and `preflight add-finding` in `cfp/scripts/cfp_store.py`

### Reviewer agent and skills

- [x] T043 [P] [US1] Write `cfp/agents/committee-reviewer.md`: frontmatter (name, description, tools Read only), persona of a KubeCon-style program committee member, instructions to read only the packet, score each criterion on the rubric scale with half steps, write two-sentence comments, lower scores for the listed rejection reasons and AI-sounding text, compare against the calibration examples, never rewrite fields, and return exactly one JSON object matching the reviewer schema in contracts/scripts.md
- [x] T044 [US1] Write `cfp/skills/committee-review/SKILL.md`: given a proposal id, run `review packet`, write the packet to a temp file in the session scratchpad, spawn the `cfp:committee-reviewer` agent with the packet, extract the first JSON object from the agent's reply (the agent may wrap it in prose), validate it against the reviewer schema, on a missing criterion or unparseable reply re-run the agent once with the validation error quoted, and if it still fails end the round with a message naming the problem instead of recording a score, otherwise run `review record`, present scores, comments, verdict, and suggestions in a compact table, and return the verdict and suggestions to the caller
- [x] T045 [US1] Write `cfp/skills/draft/SKILL.md` implementing the twelve-step flow from contracts/commands.md (profile and event selection with inline override creation via `event write` or the profile skill, deadline warning, session type with limits, input source including `--from` material, story interview driven by `talk complete`, angles per `knowledge-base/guidance/abstract-angles.md`, per-field drafting per field guidance and `knowledge-base/guidance/benefits-field.md`, bio chooser with counts and shortening, resources chooser with recordings first, committee review loop bounded by the `review_rounds` value from `config show` (when the limit is reached without a pass, list the remaining weaknesses and ask whether to continue, accept as is, or park the proposal as draft), voice pass via `prose:humanizer` with skip notice and inline fallback, over-limit shortening, pre-flight with audience-level comparison, `status ready-check` and `status set --to ready`, paste view); every step saves through the CLI so `--proposal` resumes, and when started without `--proposal` the skill lists proposals in status `draft` (`proposal list --status draft`) and offers to resume one before starting new work; `allowed-tools` Bash, Read, AskUserQuestion, Skill, Agent, WebFetch
- [x] T046 [P] [US1] Write `cfp/commands/draft.md` delegating to the `cfp:draft` skill with argument-hint `[--profile <id>] [--event <id>] [--talk <id>] [--proposal <id>] [--from <path or URL>]`

**Checkpoint**: `make test` passes; quickstart Scenario 1 produces a ready proposal and paste view.

---

## Phase 4: User Story 2 - Maintain bios and speaker resources (Priority: P2)

**Goal**: Create, list, edit, and delete bio variations and speaker resources through `/cfp:bio`

**Independent Test**: From an empty store, `/cfp:bio new` twice and `/cfp:bio resource add` once yield two bios with counts and one resource in `/cfp:bio list` (quickstart Scenario 2)

- [x] T047 [US2] Write `cfp/skills/bio/SKILL.md`: subactions `new` (ask emphasis, target length, optional source material; draft third person in the configured voice using `prose:humanizer` when available; show count; edit loop; `bio write`), `list` (`bio list` as a table with name, emphasis, chars, updated), `edit <name>`, `delete <name>` (confirm), `resource add` (ask type, title, link, date; `resource write`; recommend a recording when none exists), `resource list`, `resource delete <id>`; `allowed-tools` Bash, Read, AskUserQuestion, Skill
- [x] T048 [P] [US2] Write `cfp/commands/bio.md` delegating to the `cfp:bio` skill with argument-hint `[new | list | edit <name> | delete <name> | resource add | resource list | resource delete <id>]`

**Checkpoint**: quickstart Scenario 2 passes; in Scenario 1 the bio chooser shows counts against 500 and offers shortening.

---

## Phase 5: User Story 3 - Create or refresh a conference profile by research (Priority: P3)

**Goal**: Research a conference's public CFP pages and screenshots into an approved profile or event override through `/cfp:profile`

**Independent Test**: `/cfp:profile new <public CFP URL>` ends with an approved profile directory where every item is labeled verified with a source or unverified; `/cfp:profile refresh kubecon --event kubecon-eu-2027 --screenshots <png>` marks screenshot-derived limits as `screenshot` without changing the family profile unless approved (quickstart Scenario 3)

- [x] T049 [US3] Write `cfp/skills/profile/SKILL.md`: subactions `new` (WebSearch for the CFP page when given a name, WebFetch CFP and reviewer guideline pages, Read screenshots, build a draft JSON following `knowledge-base/guidance/profile-research.md` and the profile schema in contracts/store-files.md, present each section via AskUserQuestion for approve, edit, or re-research, write with `profile write` and `event write`, `profile approve`; when research finds no public CFP page or the form is login-walled, build a minimal profile from what the user enters, mark every item `unverified`, and suggest screenshots), `refresh <id> [--event <id or URL>] [--screenshots <paths>]` (research one edition, `event write` with `approved: false`, per-section approval, ask before any family profile change, screenshot limits set `limit_status: screenshot` and `source: screenshot:<file>`; when a screenshot value contradicts a public page, the screenshot value wins and the conflict is recorded in the profile's `## Notes` section), `show <id> [--event <id>]` (`profile show`), `list` (`profile list` with days to close); `allowed-tools` Bash, Read, AskUserQuestion, WebSearch, WebFetch, Write
- [x] T050 [P] [US3] Write `cfp/commands/profile.md` delegating to the `cfp:profile` skill with argument-hint `[new <name or URL> | refresh <id> [--event <id>] [--screenshots <paths>] | show <id> | list]`

**Checkpoint**: quickstart Scenario 3 passes; `profile validate` reports no problems for the researched profile.

---

## Phase 6: User Story 4 - Track proposal lifecycle and reuse past work (Priority: P4)

**Goal**: Move proposals through submitted, accepted, rejected, withdrawn, presented; feed accepted texts into calibration examples; reopen rejected work for another event

**Independent Test**: `/cfp:status set` through submitted and rejected, `/cfp:status reopen` into a new event with the story pre-filled, then submitted and accepted on the new proposal adds an example to `profiles/kubecon/examples/` (quickstart Scenario 4)

- [x] T051 [US4] Write `cfp/skills/status/SKILL.md`: subactions `list [--status <s>]` (`proposal list` rendered as a table grouped by status with event, dates, days to CFP close for drafts and ready), `set <id> <status> [--date <d>]` (`status set`, show side effects, explain disallowed transitions with allowed targets), `reopen <id> [--event <id>]` (load the source proposal, invoke the `cfp:draft` skill with `--talk <talk>` and the target event, show the old fields for reference during drafting); `allowed-tools` Bash, Read, AskUserQuestion, Skill
- [x] T052 [P] [US4] Write `cfp/commands/status.md` delegating to the `cfp:status` skill with argument-hint `[list [--status <s>] | set <proposal-id> <status> [--date <d>] | reopen <proposal-id> [--event <id>]]`

**Checkpoint**: quickstart Scenario 4 passes; the next `review packet` for kubecon lists the accepted example.

---

## Phase 7: User Story 5 - Pre-flight rule check before submission (Priority: P5)

**Goal**: Standalone `/cfp:check` that runs the hard rules, the audience-level comparison, and the counts on any stored proposal

**Independent Test**: With three submitted proposals for an event, `/cfp:check` on a fourth reports the submission limit (disqualify) citing the LF URL; a presented outing within a year yields the repeat warning; a track outside the event list yields the track finding with the list (quickstart Scenario 5)

- [x] T053 [US5] Write `cfp/skills/check/SKILL.md`: pick the proposal (argument or `proposal list`), run `preflight`, compare the abstract against the chosen audience level and add a `warn` finding via `preflight add-finding --rule audience-level` when they disagree, run `count`, print findings with severity and source, over-limit fields, missing required fields, and the `manual` rules for the committee review; offer to open `/cfp:draft --proposal <id>` for fixes; `allowed-tools` Bash, Read, AskUserQuestion
- [x] T054 [P] [US5] Write `cfp/commands/check.md` delegating to the `cfp:check` skill with argument-hint `<proposal-id>`

**Checkpoint**: quickstart Scenario 5 passes; `test_preflight.py` covers every rule kind (SC-006).

---

## Phase 8: Polish and Cross-Cutting Concerns

- [x] T055 [P] Write `README.md`: what the plugin does, install via `make install`, `/cfp:init` first run, command overview table, store layout, how to confirm KubeCon limits with screenshots, voice pass requirements, development (uv venv, make test)
- [x] T056 [P] Add `cfp/scripts/test/test_seed_profile.py` asserting the shipped KubeCon profile and both events pass `profile validate`, carry `approved: true`, have 13 and 11 tracks, and that every field limit is `unverified`
- [x] T057 Run `make lint-dashes`, `make validate`, `make test`, and `make test-hook`; fix any failure
- [x] T058 (script-level smoke test and timing done, see quickstart-results.md; interactive Scenarios 1 to 6 and the Obsidian check are listed there for the user) Walk through quickstart.md Scenarios 1 to 6 in a Claude Code session against a scratch store and record outcomes in `specs/001-cfp-plugin/quickstart-results.md`; for SC-008 also open the scratch store as an Obsidian vault, confirm a profile, a talk, and a proposal render with their properties, edit one bio's text in Obsidian, and confirm `/cfp:bio list` shows the new count without errors; for the performance goal in plan.md, generate 300 proposal files from the template in a scratch store, time `proposal list` and `preflight` once with `time`, and record the wall-clock numbers (expected under one second each)

---

## Dependencies and Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies
- **Foundational (Phase 2)**: depends on Phase 1; blocks every user story
- **US1 (Phase 3)**: depends on Phase 2; the MVP
- **US2 (Phase 4)**: depends on Phase 2 only (bio and resource CLI live in Phase 2)
- **US3 (Phase 5)**: depends on Phase 2 only
- **US4 (Phase 6)**: depends on Phase 2 (lifecycle CLI) and Phase 3 (reopen invokes the draft skill)
- **US5 (Phase 7)**: depends on Phase 3 (preflight and count CLI)
- **Polish (Phase 8)**: depends on all story phases

### Within Each Phase

- Test file before the module it covers (T008 before T009, and so on); the test must fail before the module is implemented
- Library module before the CLI wiring that exposes it
- CLI subcommands before the skill that calls them
- T030 (shared preamble) before any `SKILL.md` that includes it (T028, T044, T045, T047, T049, T051, T053)
- Skill before its command wrapper

### Parallel Opportunities

- Phase 1: T002 to T007 in parallel after T001
- Phase 2: all test files (T008, T010, T012, T014, T016, T018) in parallel; knowledge base tasks T021 to T027 in parallel with the library work; T029 in parallel with T028
- Phase 3: test files T031, T033, T035, T037, T039, T041 in parallel; T043 in parallel with the library work; T046 with T045
- Phases 4, 5, 6, 7: each command wrapper in parallel with its skill; US2 and US3 can run in parallel with US1 once Phase 2 is done

---

## Parallel Example: Phase 2 library

```bash
# Write all foundation tests together:
Task: "Write cfp/scripts/test/test_frontmatter.py"
Task: "Write cfp/scripts/test/test_config.py"
Task: "Write cfp/scripts/test/test_store.py"
Task: "Write cfp/scripts/test/test_profile.py"
Task: "Write cfp/scripts/test/test_lifecycle.py"
Task: "Write cfp/scripts/test/test_bio_resource.py"

# Write the knowledge base in parallel with the library:
Task: "Write cfp/knowledge-base/profiles/kubecon/profile.md"
Task: "Write cfp/knowledge-base/profiles/kubecon/events/kubecon-eu-2027.md and kubecon-na-2026.md"
Task: "Write cfp/knowledge-base/guidance/abstract-angles.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (setup) and Phase 2 (foundation, seed profile, init)
2. Complete Phase 3 (draft flow with review, voice pass, pre-flight, paste view)
3. Validate with quickstart Scenario 1
4. The plugin is already useful for the open KubeCon EU 2027 CFP at this point

### Incremental Delivery

1. Phase 4 adds reusable bios and resources
2. Phase 5 adds profile research for other conferences and screenshot-verified limits
3. Phase 6 adds the lifecycle and resubmission path
4. Phase 7 adds the standalone check
5. Phase 8 documents and validates everything

---

## Notes

- Total tasks: 58 (Setup 7, Foundational 23, US1 16, US2 2, US3 2, US4 2, US5 2, Polish 4)
- Commit after each task or logical group
- Keep skills under roughly 400 lines; move long guidance into `knowledge-base/guidance/`
- Never write em-dash or en-dash characters; `make lint-dashes` enforces it
