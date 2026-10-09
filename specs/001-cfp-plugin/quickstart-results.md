# Quickstart Results: 001-cfp-plugin

**Date**: 2026-10-09 | **Environment**: macOS, Python 3.14.8 (scripts run with `python3 -I`), pytest in `~/.venvs/cc-cfp`

The automated parts of quickstart.md were executed during implementation (task T058). The interactive scenarios need a Claude Code session with the plugin installed and are listed at the end for the user.

## Setup checks

| Check | Command | Result |
|---|---|---|
| Manifests | `make validate` | Both manifests valid (root marketplace and `cfp/`) |
| Unit tests | `make test` | 131 passed |
| Hook | `make test-hook` | JSON with `<cfp-context>` printed; with a configured store the block carries `store-initialized: true` |
| Dashes | `make lint-dashes` | No em-dash or en-dash in `cfp/` or `README.md` |

## Script-level smoke test (no model involved)

Run against a scratch store with `HOME` pointed at a scratch directory so the real `~/.config/cc-cfp/config.json` stayed untouched, and `--today 2026-10-09`.

| Step | Expected (quickstart.md) | Observed |
|---|---|---|
| `config init --seed-dir cfp/knowledge-base/profiles` | `seeded_profiles: ["kubecon"]` | `ok: true`, `seeded_profiles: ["kubecon"]`, folder tree and `config.md` created |
| `profile list` | kubecon approved with events eu-2027 and na-2026 | `kubecon` approved; `kubecon-eu-2027` approved, 2 days to close; `kubecon-na-2026` approved, closed 131 days ago |
| `profile show --profile kubecon --event kubecon-eu-2027` | 13 tracks, 80 minute tutorial, limits unverified | 13 tracks; tutorial 80; limits title 75, abstract 1300, benefits 1000, all `unverified` |
| SC-006 submission limit: three submitted proposals plus a fourth, then `preflight` | `ok: false` with a `submission-limit` disqualify finding citing the LF CFP URL | `passed: false`; finding `submission-limit`, severity `disqualify`, source `https://events.linuxfoundation.org/kubecon-cloudnativecon-europe/program/cfp/` |
| Repeat rule: talk with a `presented` outing in the kubecon family dated 2026-03-25, proposal for NA 2026 with an unknown track | repeat finding and track mismatch | `repeat-one-year` disqualify (no previously-presented note yet) and `track-in-event` disqualify listing the event's tracks |
| Broken front matter: `talks/broken.md` without closing `---` | path and problem reported, other files still listed | 4 talks listed; `problems` names `broken.md` with "missing closing '---' for front matter" |
| `pasteview --format markdown` on an undrafted proposal | fields in form order with counts and flags | Markdown header, approximate-limit warning, missing required fields warning, 11 fields in form order, bio last |
| `status set --to accepted` on a submitted proposal | calibration example added | Side effect reports the new example file; `example list` shows it first, then the LF sample |

Every rule kind is additionally covered one at a time in `cfp/scripts/test/test_preflight.py` (submission_limit, repeat_within_months with the month boundary, track_in_event, speaker_count, all_men_panel, multi_company_panel, vendor_pitch and custom as manual).

## Performance goal (plan.md: script calls under one second for a few hundred files)

A scratch store was filled with 300 proposals and 300 talks generated from the templates (abstract of about 1000 characters each, 43 in status submitted).

| Command | Wall clock |
|---|---|
| `proposal list` (300 proposals returned) | 0.071 s |
| `preflight --proposal kubecon-eu-2027--talk-000` (scans all proposals for the submission limit) | 0.078 s |

Both are far under the one second goal. Measured with the shell `time` builtin, including interpreter startup.

## Interactive scenarios left for the user

These need a Claude Code session with the plugin installed (`make install`) and were not run by the implementation agent:

1. **Scenario 1 (US1, SC-001 to SC-003)**: `/cfp:init` into a scratch folder, then `/cfp:draft` from a one-line idea through story interview, angles, field drafting, committee review (five scored criteria with comments), voice pass or skip notice, pre-flight, and paste view. Expected: `proposals/kubecon-eu-2027--<talk>.md` in status `ready`, every required field present and under its limit, at least one review round, under 30 minutes.
2. **Scenario 2 (US2)**: `/cfp:bio new` twice (cloud-native 450, ai 800), `/cfp:bio resource add` with a recording, `/cfp:bio list`. Then in Scenario 1 the bio chooser shows counts against 500 and offers to shorten the 800 one.
3. **Scenario 3 (US3, SC-005)**: `/cfp:profile new <public CFP URL>` with per-section approval and one rejected item entered manually; `/cfp:profile refresh kubecon --event kubecon-eu-2027 --screenshots <png>`. Expected: new profile approved with every item labeled verified or unverified; screenshot-derived limits carry `limit_status: screenshot`; the family profile unchanged unless approved.
4. **Scenario 4 (US4, SC-004, SC-007)**: `/cfp:status set <proposal> submitted`, then `rejected`, `/cfp:status reopen <proposal> --event kubecon-na-2026` with the story pre-filled and under 10 minutes, then `submitted` and `accepted` on the new proposal; a later `/cfp:draft` for kubecon lists the accepted example in the review packet.
5. **Scenario 5 (US5, SC-006)**: `/cfp:check` on a fourth proposal after three submitted ones, on a talk presented within a year, and on a proposal with a track outside the event list. The script-level equivalents above already pass.
6. **Scenario 6 (edge cases)**: delete `~/.config/cc-cfp/config.json` and run `/cfp:status list` (init offered); break a talk file's front matter and run `/cfp:status list` (path and problem reported, others listed); `/cfp:draft` for an event whose `cfp_close` is in the past (warning, drafting continues); `/cfp:draft --event kubecon-india-2026` (inline override creation offered).
7. **SC-008 (Obsidian)**: open the scratch store as an Obsidian vault, confirm a profile, a talk, and a proposal render with their properties, edit one bio's text in Obsidian, and confirm `/cfp:bio list` shows the new count without errors. The parser round-trips the seed profile, events, and templates losslessly, and `bio list` recounts characters from the body on every call, so a manual edit is picked up without a rewrite.
