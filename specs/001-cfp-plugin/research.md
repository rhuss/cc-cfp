# Research: CFP and Bio Plugin

**Date**: 2026-10-09 | **Feature**: 001-cfp-plugin

Each entry records a decision, the rationale, and the alternatives considered. Domain research on KubeCon (formats, fields, rubric, rules, dates) is in `brainstorm/research/kubecon-cfp-research.md` and is not repeated here.

## R1. Plugin layout and conventions

**Decision**: Nested layout `cc-cfp/cfp/` with `commands/`, `skills/`, `agents/`, `knowledge-base/`, `hooks/scripts/`, `scripts/`, plus root `Makefile` and `.claude-plugin/marketplace.json`. Commands are one-paragraph wrappers that invoke a skill with `$ARGUMENTS`.

**Rationale**: Matches `PLUGIN-ARCHITECTURE.md` and the sibling `cc-blog` plugin, so install, validate, and hook patterns are already proven for this user. Thin commands keep the workflow text in one place (the skill) and make skills reusable from other skills.

**Alternatives considered**: Flat layout (plugin.json at repo root): rejected, the architecture guide documents migration away from it. Everything inside commands with no skills: rejected, the draft flow is long and needs to call the review and bio flows internally.

## R2. Script runtime: stdlib only, no venv

**Decision**: Python 3.10+ standard library only. A single entry point `scripts/cfp_store.py` with subcommands, always invoked as `python3 -I "$PLUGIN_ROOT/scripts/cfp_store.py" <subcommand> ...`. All output is one JSON object on stdout; errors are `{"ok": false, "error": "..."}` on stdout with exit code 1 (usage errors exit 2), as defined in contracts/scripts.md.

**Rationale**: The architecture guide's venv bootstrap exists to install third-party packages. Nothing here needs one: front matter is simple, counting is trivial, rule evaluation is plain logic. Dropping the venv removes a setup step, an entire skill, and a class of "environment not found" failures. The `-I` flag isolates the interpreter from the current directory, which matters because the scripts read user-controlled files.

**Alternatives considered**: `python-frontmatter` plus PyYAML in a venv: rejected, the schemas only need scalars, lists, and one nested map level; a 150-line parser covers it and is fully tested. Shell plus `yq`: rejected, `yq` is not guaranteed on other users' machines and multi-line editing in shell is fragile.

## R3. Front matter format and parser scope

**Decision**: YAML front matter delimited by `---`, restricted to: string, integer, boolean, ISO date scalars; flat lists (`- item`); one level of nested maps (`fields:` holding a list of maps for profile fields). Block scalars (`|`) for multi-line values. The parser rejects anything outside this subset with a clear error that names the file and line (spec edge case for invalid front matter).

**Rationale**: Obsidian renders this subset as properties. Keeping the subset small makes hand edits safe and the parser testable. Profile field definitions are the only nested structure and fit "list of flat maps".

**Alternatives considered**: JSON front matter: rejected, Obsidian support is weaker and hand editing is worse. TOML: rejected, Obsidian does not render it.

## R4. Store layout

**Decision**:

```text
<store>/
├── config.md                      # speaker, voice, review rounds (front matter only)
├── profiles/<family>/
│   ├── profile.md                 # family profile
│   ├── events/<event-slug>.md     # per-event overrides
│   └── examples/<slug>.md         # calibration examples (accepted texts)
├── talks/<talk-slug>.md
├── proposals/<event-slug>--<talk-slug>.md
├── bios/<bio-name>.md
└── resources/<resource-slug>.md
```

User-level config at `~/.config/cc-cfp/config.json` holds only `{"store": "<absolute path>"}` (and the override env var `CFP_STORE` for tests).

**Rationale**: One folder per entity type keeps Obsidian navigation and search obvious. The proposal name encodes event and talk so the file list reads as a submission log. The store path must live outside the store (chicken and egg), everything else travels with the data, which the spec requires (FR-002a).

**Alternatives considered**: One big index file: rejected, conflicts with hand editing and Obsidian linking. Proposals nested under talks: rejected, the per-event listing (pre-flight, status view) is the more common access path.

## R5. Seed profile delivery

**Decision**: The KubeCon profile ships under `cfp/knowledge-base/profiles/kubecon/` and `/cfp:init` copies it into `<store>/profiles/kubecon/` with `approved: true` and `seed_version` set. The plugin never reads profiles from the knowledge base at draft time. A later `/cfp:profile refresh kubecon` can re-merge seed updates on request.

**Rationale**: The user will edit limits after seeing the live form (unverified limits must become verified). Editing a file inside the installed plugin would be lost on update, so the store copy is the source of truth.

**Alternatives considered**: Read seed from the plugin with user overrides layered on top: rejected, two sources for one profile make "what is current" unclear and complicate the approval rule.

## R6. Committee review mechanism

**Decision**: The draft skill builds a review packet (rubric with scale, pass threshold, rejection reasons, up to three calibration examples, the drafted fields, the stated audience level and track) and spawns a fresh subagent using the `committee-reviewer` agent definition. The agent returns strict JSON: per-criterion score, per-criterion comment, overall verdict, and up to five concrete revision suggestions each tagged with a field name. The skill passes the JSON to `cfp_store.py review record` which stores the round and computes pass or revise against the threshold (default: average at least 4.0 and no criterion below 3.0).

**Rationale**: A fresh subagent has no drafting context and no incentive to approve its own work, which mirrors a real reviewer. Numeric scores plus comments satisfy the spec's scoring requirement and make the verdict rule deterministic in a script.

**Alternatives considered**: Inline self-review in the drafting conversation: rejected, anchoring on the draft produces inflated scores. Multiple reviewer agents averaged: deferred, costs more and the single reviewer plus revision loop already covers the requirement.

## R7. Voice pass integration

**Decision**: After a pass verdict, the draft skill invokes the `prose:humanizer` skill once per prose field with the voice profile name from `config.md`. If the Skill invocation is unavailable (plugin missing) the step is skipped with a notice. If the invocation returns usage text instead of a rewrite (a failure mode `cc-blog` documents), the skill applies the humanizer's core rules inline (no AI vocabulary, no rule-of-three padding, no inflated symbolism, varied sentence length) and says so. Character counts are recomputed afterwards via `cfp_store.py count`.

**Rationale**: Reuses the user's existing voice infrastructure. The inline fallback prevents silently dropping voice enforcement.

**Alternatives considered**: Running the humanizer on the whole paste view at once: rejected, per-field limits need per-field recounting and the title must not be rewritten freely.

## R8. Profile research inputs

**Decision**: `/cfp:profile` uses WebSearch to find the CFP page for a conference name, WebFetch to read CFP pages and reviewer guideline pages, and the Read tool for screenshot image files (pasted images arrive in the conversation directly). Extracted items are written into a draft profile with `source:` (URL or `screenshot:<file>`) and `verified:` fields. The user approves via AskUserQuestion per section (session types, fields, rules, dates), then the draft is saved with `approved: true`.

**Rationale**: These are the tools available inside a Claude Code session; no external scraping dependency is needed. Per-section approval keeps the review manageable and satisfies FR-009.

**Alternatives considered**: Playwright automation of Sessionize behind login: rejected, the spec forbids interacting with submission sites and the form is login-walled.

## R9. Testing approach

**Decision**: pytest tests for every `cfplib` module against a temporary store created in `tmp_path`, including fixtures that copy the seed profile. A dev venv is created with `uv venv ~/.venvs/cc-cfp` and `uv pip install -r cfp/requirements-dev.txt`; `make test` runs `~/.venvs/cc-cfp/bin/python -m pytest cfp/scripts/test`. `make validate` runs `claude plugin validate` on both manifests. `make test-hook` pipes a sample prompt through the context hook. Interactive skill behavior is validated by the quickstart scenarios.

**Rationale**: Follows the user's `uv` mandate and venv location rule. Keeps model-driven behavior out of unit tests while covering all deterministic logic.

**Alternatives considered**: unittest only: workable but pytest fixtures (`tmp_path`) make store tests much shorter.

## R10. Slug and identity rules

**Decision**: Slugs are lowercase ASCII, words joined by hyphens, max 60 characters, generated from the title (talks), the bio name, the resource title, or the event name. Collisions append `-2`, `-3`. Files are identified by path; front matter also carries an `id` equal to the slug for Obsidian queries. Proposal file name is `<event-slug>--<talk-slug>.md`; a second proposal of the same talk for the same event is refused (one proposal per talk per event, the user can withdraw and reopen).

**Rationale**: Human-readable names in the vault, stable references in front matter, no hidden IDs.

**Alternatives considered**: UUIDs in front matter: rejected, unreadable in Obsidian and unnecessary at this scale.
