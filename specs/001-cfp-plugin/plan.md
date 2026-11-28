# Implementation Plan: CFP and Bio Plugin for Conference Submissions

**Branch**: `001-cfp-plugin` | **Date**: 2026-10-09 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-cfp-plugin/spec.md`

## Summary

Build the `cfp` Claude Code plugin: six slash commands (`/cfp:init`, `/cfp:profile`, `/cfp:bio`, `/cfp:draft`, `/cfp:check`, `/cfp:status`) backed by skills that run the interactive flows, a small set of stdlib-only Python scripts for the deterministic parts (store access, front matter, character counts, rule evaluation, paste view, status transitions), a knowledge base holding the shipped KubeCon profile, and a context hook that injects the plugin root and store path. All user data lives as markdown with YAML front matter in a configurable Obsidian vault folder (Superseded by feature 002: the default store is `<data folder>/store` and the config folder follows XDG; see specs/002-xdg-config-store/spec.md). Drafting is talk-centric: a talk file holds the story, a proposal file holds the per-field rendering for one event, and the committee review runs in a fresh subagent that only sees the rubric and the draft.

## Technical Context

**Language/Version**: Markdown (commands, skills, knowledge base) plus Python 3.10 or newer for scripts (stdlib only, no third-party runtime dependencies)

**Primary Dependencies**: Claude Code plugin system (commands, skills, hooks, Skill and Agent tools, AskUserQuestion, WebSearch, WebFetch, image Read); optional `prose` plugin (`prose:humanizer` skill) for the voice pass

**Storage**: Markdown files with YAML front matter in `<store>` (default `~/Obsidian/<vault>/Talks`, configured at first use); user-level config in `~/.config/cc-cfp/config.json`. Superseded by feature 002: the default store is `<data folder>/store` and the config folder follows XDG; see specs/002-xdg-config-store/spec.md.

**Testing**: pytest for scripts (dev-only dependency installed with `uv` into `~/.venvs/cc-cfp`); `claude plugin validate` for manifests; hook smoke test via Makefile; quickstart scenarios run manually in a Claude Code session

**Target Platform**: Claude Code CLI on macOS and Linux

**Project Type**: Claude Code plugin (nested subdirectory layout per `PLUGIN-ARCHITECTURE.md`)

**Performance Goals**: Script calls return in under one second for a store with up to a few hundred files; interactive flows stay within the spec's 30 minute (new proposal) and 10 minute (reuse) budgets

**Constraints**: No auto-submission; no network calls except profile research (public pages) and the user's explicit links; scripts must never require a virtual environment at runtime; store files must stay hand-editable and Obsidian-renderable; no em-dash or en-dash characters in generated prose

**Scale/Scope**: One speaker per store; tens of talks, tens of proposals per year, a handful of profiles, under ten bio variations

## Global Constraints

Every task inherits these. The first four are copied from the spec; the rest are project conventions.

- FR-001: all data (profiles, talks, proposals, bios, resources, store configuration) is plain markdown with structured front matter in a user-configurable folder.
- FR-003: every stored file remains readable and editable by hand; manual edits that keep the front matter valid are tolerated.
- FR-036: the plugin never submits anything to a conference website or interacts with the submission site on the user's behalf.
- FR-037 and FR-038: no co-speaker bio or profile management (co-speaker details are free text on the proposal); no slides, speaker notes, or post-acceptance material.
- Python 3.10 or newer, standard library only, always invoked as `python3 -I`; no virtual environment at runtime.
- Every CLI subcommand prints exactly one JSON object on stdout (contracts/scripts.md); scripts make no network calls.
- No em-dash or en-dash characters in any markdown, prose, or string the user reads.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

`.specify/memory/constitution.md` is the unfilled template (placeholder principles only). No project-specific gates apply. The plan follows the conventions the user has established for sibling plugins instead (nested layout, thin commands delegating to skills, Python scripts under `scripts/`, Makefile targets `validate`, `install`, `test`, `test-hook`). Re-check after Phase 1: no violations, nothing to justify in Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/001-cfp-plugin/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── commands.md      # Slash command contracts (arguments, prompts, outputs)
│   ├── scripts.md       # Python script CLI contract (subcommands, JSON in/out)
│   └── store-files.md   # Front matter schemas for every store file type
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
cc-cfp/
├── .claude-plugin/
│   └── marketplace.json              # Local marketplace pointing at ./cfp
├── Makefile                          # validate, install, uninstall, test, test-hook, clean
├── .gitignore
├── README.md                         # Install, configure, command overview
│
└── cfp/                              # Plugin source (what Claude installs)
    ├── .claude-plugin/
    │   └── plugin.json
    ├── hooks.json                    # UserPromptSubmit -> hooks/scripts/context-hook.py
    ├── hooks/scripts/
    │   └── context-hook.py           # Injects <cfp-context>: plugin root, store path, config status
    ├── commands/                     # Thin wrappers, each delegates to a skill
    │   ├── init.md
    │   ├── profile.md
    │   ├── bio.md
    │   ├── draft.md
    │   ├── check.md
    │   └── status.md
    ├── skills/
    │   ├── _shared/preamble.md       # Step 0 shared by every skill: parse <cfp-context>, offer init, CLI invocation pattern
    │   ├── init/SKILL.md             # First-use setup: store path, speaker, voice, seed profile copy
    │   ├── profile/SKILL.md          # Research, screenshots, draft, approval, event refresh
    │   ├── bio/SKILL.md              # Bio variations and speaker resources
    │   ├── draft/SKILL.md            # Interactive drafting pipeline (US1)
    │   ├── committee-review/SKILL.md # Subagent prompt builder and verdict handling
    │   ├── check/SKILL.md            # Standalone pre-flight (US5)
    │   └── status/SKILL.md           # Lifecycle transitions and listing (US4)
    ├── agents/
    │   └── committee-reviewer.md     # Fresh-context reviewer persona (scores rubric, JSON out)
    ├── knowledge-base/
    │   ├── profiles/kubecon/         # Shipped seed profile (copied into the store on init)
    │   │   ├── profile.md
    │   │   ├── events/kubecon-eu-2027.md
    │   │   ├── events/kubecon-na-2026.md
    │   │   └── examples/lf-sample-container-runtime.md
    │   ├── templates/                # Front matter templates for talk, proposal, bio, resource, profile, event
    │   └── guidance/
    │       ├── abstract-angles.md    # How to generate problem-first, story, contrarian angles
    │       ├── benefits-field.md     # How to write a reviewer-only relevance field
    │       └── profile-research.md   # What to look for on CFP pages and in screenshots
    ├── scripts/
    │   ├── cfp_store.py              # Single CLI entry point (subcommands, JSON output)
    │   ├── cfplib/
    │   │   ├── __init__.py
    │   │   ├── frontmatter.py        # Minimal YAML front matter read/write (stdlib)
    │   │   ├── config.py             # User config and store config resolution
    │   │   ├── store.py              # Paths, slugs, generic load and save, list with parse problems
    │   │   ├── bios.py               # Bio variation and speaker resource read, write, list, delete
    │   │   ├── profile.py            # Profile plus event override merge, approval checks, examples
    │   │   ├── talks.py              # Talk write, show, list, completeness check
    │   │   ├── proposals.py          # Proposal create, field and meta updates, bio snapshot
    │   │   ├── counts.py             # Character counts and limit evaluation
    │   │   ├── review.py             # Review packet build, round record and verdict, history
    │   │   ├── preflight.py          # Hard rule evaluation and manual findings
    │   │   ├── pasteview.py          # Paste view rendering
    │   │   └── lifecycle.py          # Status transitions, calibration append, outing record
    │   └── test/
    │       ├── conftest.py           # tmp_store, seeded_store, run_cli fixtures
    │       ├── test_frontmatter.py
    │       ├── test_config.py
    │       ├── test_store.py
    │       ├── test_bio_resource.py
    │       ├── test_profile.py
    │       ├── test_lifecycle.py
    │       ├── test_cli_foundation.py
    │       ├── test_talk.py
    │       ├── test_proposal.py
    │       ├── test_counts.py
    │       ├── test_pasteview.py
    │       ├── test_review.py
    │       ├── test_preflight.py
    │       └── test_seed_profile.py
    └── requirements-dev.txt          # pytest only
```

**Structure Decision**: Nested plugin layout as used by the user's other cc-* plugins. Commands are thin wrappers; skills hold the interactive workflows; one Python CLI (`cfp_store.py`) with subcommands wraps a small library so that every deterministic step (counting, rule checks, status changes, rendering) is testable with pytest and never depends on model judgment. No virtual environment at runtime because the scripts use only the standard library; a dev venv exists only for pytest.

## Phase 0: Research Summary

See [research.md](research.md). Decisions: stdlib-only scripts invoked with `python3 -I`; YAML front matter handled by a minimal parser supporting scalars, lists, and one level of nested maps (enough for every schema in data-model.md); committee review in a fresh subagent with JSON output; voice pass through `prose:humanizer` with an inline fallback; profile research with WebSearch, WebFetch, and image Read; seed profile copied into the store at init so user edits never touch the plugin; store default inside the Obsidian vault (Superseded by feature 002: the default store is `<data folder>/store` and the config folder follows XDG; see specs/002-xdg-config-store/spec.md).

## Phase 1: Design Summary

- [data-model.md](data-model.md): entities, front matter fields, relationships, state machine for proposal status, validation rules.
- [contracts/commands.md](contracts/commands.md): what each slash command accepts, asks, and produces.
- [contracts/scripts.md](contracts/scripts.md): `cfp_store.py` subcommands with JSON input and output.
- [contracts/store-files.md](contracts/store-files.md): file naming and front matter schema per store file type.
- [quickstart.md](quickstart.md): end-to-end validation scenarios mapped to the spec's user stories.

## Complexity Tracking

No constitution violations. Nothing to justify.
