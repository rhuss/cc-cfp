# Quickstart: Validating the CFP Plugin

**Feature**: 001-cfp-plugin | **Date**: 2026-10-09

This guide proves the feature end to end. Automated checks come first; the interactive scenarios map to the spec's user stories and run in a Claude Code session.

## Prerequisites

- Claude Code CLI with plugin support
- Python 3.10 or newer on PATH
- `uv` for the dev environment (tests only)
- Optional: the `prose` plugin installed, for the voice pass scenario

## Setup

```bash
cd cc-cfp
uv venv ~/.venvs/cc-cfp
uv pip install --python ~/.venvs/cc-cfp/bin/python -r cfp/requirements-dev.txt
make validate      # claude plugin validate on both manifests
make test          # pytest over cfp/scripts/test
make test-hook     # context hook emits <cfp-context>
make install       # marketplace add + plugin install
```

Expected: `validate` reports both manifests valid; `test` passes with zero failures; `test-hook` prints JSON containing `<cfp-context>`; `install` reports the plugin installed.

## Script-level smoke test (no model involved)

Uses a temporary store so the vault is untouched.

```bash
export CFP_STORE=$(mktemp -d)/store
PLUGIN=cfp
python3 -I $PLUGIN/scripts/cfp_store.py config init --store "$CFP_STORE" \
  --speaker-name "Test Speaker" --seed-dir $PLUGIN/knowledge-base/profiles
python3 -I $PLUGIN/scripts/cfp_store.py profile list
python3 -I $PLUGIN/scripts/cfp_store.py profile show --profile kubecon --event kubecon-eu-2027
```

Expected: `config init` reports `seeded_profiles: ["kubecon"]`; `profile list` shows `kubecon` approved with events `kubecon-eu-2027` and `kubecon-na-2026`; `profile show` returns 13 tracks for EU 2027, a tutorial of 80 minutes, and fields with `limit_status: unverified`.

Pre-flight rule check (SC-006):

```bash
# create a talk, a proposal, and three submitted proposals for the same event, then
python3 -I $PLUGIN/scripts/cfp_store.py preflight --proposal kubecon-eu-2027--fourth-talk
```

Expected: `ok: false` with a `submission-limit` finding of severity `disqualify` citing the LF CFP URL. The pytest suite covers every rule kind one at a time.

## Scenario 1: Draft a KubeCon proposal from an idea (US1, SC-001, SC-002, SC-003)

In a Claude Code session inside any project:

1. `/cfp:init` and accept the defaults (point the store at a scratch folder for the test).
2. `/cfp:draft`, choose `kubecon`, event `kubecon-eu-2027`, session type `session`, input "one-line idea", type a one-sentence idea.
3. Answer the story interview (problem, contribution, three takeaways, personas, what is new, prior outings: none).
4. Pick one of the offered angles.
5. Let the drafting fill title, abstract, benefits, audience level, track, case study flag, previously presented note, projects, resources, bio.
6. Observe the committee review: five scores with comments and a verdict. Accept the suggested revisions once if the verdict is revise.
7. Observe the voice pass (or the skip notice when the prose plugin is missing).
8. Observe pre-flight (no findings expected for a fresh store) and the paste view.

Expected: a file `proposals/kubecon-eu-2027--<talk>.md` with status `ready`, every required field present, every field with a known limit at or under it (counts shown in the paste view), `review_rounds` holding at least one round with all five criteria scored, and the whole flow under 30 minutes.

## Scenario 2: Bios and resources (US2)

1. `/cfp:bio new`, emphasis "cloud-native", target length 450. Edit once. Save.
2. `/cfp:bio new`, emphasis "ai", target length 800. Save.
3. `/cfp:bio resource add`, type recording, a link, a date.
4. `/cfp:bio list`.

Expected: two bios listed with name, emphasis, character count, and date; the resource appears in `resource list`. In Scenario 1 step 5, the bio chooser shows counts against the 500 limit and offers to shorten the 800 one.

## Scenario 3: Profile research (US3, SC-005)

1. `/cfp:profile new "https://events.linuxfoundation.org/kubecon-cloudnativecon-north-america/program/cfp/"` (or any public CFP page of another conference).
2. Review each section; reject one item and provide a manual value.
3. Approve.
4. `/cfp:profile refresh kubecon --event kubecon-eu-2027 --screenshots ~/Desktop/sessionize-form.png` (any screenshot of a form).

Expected: a new profile directory with `approved: true`, each item labeled verified (with URL) or unverified; after the refresh, the fields shown in the screenshot carry `limit_status: screenshot` and the family profile is unchanged unless approved.

## Scenario 4: Lifecycle and reuse (US4, SC-004, SC-007)

1. `/cfp:status set <proposal> submitted`.
2. `/cfp:status set <proposal> rejected`.
3. `/cfp:status reopen <proposal> --event kubecon-na-2026` and finish the draft; the story is pre-filled.
4. `/cfp:status set <new proposal> submitted`, then `accepted`.
5. `/cfp:draft` again for the same profile and look at the review packet or the examples section.

Expected: dates recorded on each transition; the reopened draft reuses story, bio, and resources and completes in under 10 minutes; after `accepted`, `profiles/kubecon/examples/` contains the proposal's texts and the next review packet lists it.

## Scenario 5: Pre-flight (US5, SC-006)

1. Mark three proposals for `kubecon-eu-2027` as submitted.
2. `/cfp:check` on a fourth proposal for the same event.
3. Set a talk outing of kind presented, family kubecon, dated within the last year, then `/cfp:check` a proposal of that talk for `kubecon-na-2026`.
4. Set a proposal's track to a name not in the event list, then `/cfp:check`.

Expected: submission limit finding (disqualify), repeat warning asking about the previously-presented note, track mismatch finding offering the event's list, each citing its rule source.

## Scenario 6: Edge cases

- Delete `~/.config/cc-cfp/config.json` and run `/cfp:status list`: the command offers init.
- Break the front matter of one talk file (remove the closing `---`): `/cfp:status list` reports the path and problem and still lists the others.
- Run `/cfp:draft` for an event whose `cfp_close` is in the past: a warning appears, drafting continues.
- Run `/cfp:draft` for the `kubecon` profile with `--event kubecon-india-2026` (no override): inline creation is offered.
