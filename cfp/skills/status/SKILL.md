---
name: cfp:status
description: This skill should be used when the user runs "/cfp:status", asks to "list my proposals", "show proposal status", "mark a proposal submitted", "mark accepted", "mark rejected", "mark presented", "withdraw a proposal", "set a proposal ready", or "reopen a rejected proposal for another event". Lists proposals grouped by status, changes a proposal's status with its date and side effects, and reopens rejected or withdrawn work into a new draft.
argument-hint: "[list [--status <s>] | set <proposal-id> <status> [--date <d>] | reopen <proposal-id> [--event <id>]]"
allowed-tools: ["Bash", "Read", "AskUserQuestion", "Skill"]
---

# cfp:status

Track the proposal lifecycle. Follow Step 0 and the shared rules in `skills/_shared/preamble.md` under `PLUGIN_ROOT`. Always pass `--today "<today>"` to `status set`.

## Subaction

Parse `$ARGUMENTS`:

| Arguments | Subaction |
|---|---|
| empty or `list [--status <s>]` | List proposals grouped by status |
| `set <id> <status> [--date <d>]` | Change a proposal's status |
| `reopen <id> [--event <id>]` | Start a new draft from a rejected or withdrawn proposal |

Statuses: `draft`, `ready`, `submitted`, `accepted`, `presented`, `rejected`, `withdrawn`. Anything else: show this table and ask.

## `list`

1. Run `proposal list` (add `--status <s>` when given). Report `problems` once (path and error) and continue.
2. Run `profile list` and build a map from event id to `days_to_close` (negative means the CFP is closed; `null` when the event has no close date).
3. Render one table per status in this order: draft, ready, submitted, accepted, presented, rejected, withdrawn. Skip empty groups. Columns:

| Id | Title | Profile | Event | Session type | Date | Days to close |
|---|---|---|---|---|---|---|

Profile and Event come from `profile` and `event` of each row. Date column by status: `updated` for draft, `ready_on` for ready, `submitted_on` for submitted, `decided_on` for accepted, rejected, and withdrawn, `presented_on` for presented. Fill "Days to close" only for draft and ready rows; write `closed (N days ago)` for negative values and leave other groups empty.

4. End with one line of totals per status and, when any draft or ready proposal has a closed CFP, a reminder that it can be reopened for a later edition with `/cfp:status reopen <id>`.

## `set <id> <status> [--date <d>]`

1. Run:

```bash
python3 -I "$PLUGIN_ROOT/scripts/cfp_store.py" status set \
  --proposal "<id>" --to <status> [--date <YYYY-MM-DD>] --today "<today>"
```

2. On success show `from`, `to`, `date`, and every entry of `side_effects` as its own bullet. Explain the two automatic effects when they appear: `accepted` adds the proposal's title, abstract, and reviewer-only relevance text as a calibration example to the profile (FR-033); `presented` records an outing on the talk so the one-year repeat rule applies to future proposals (FR-034).
3. For `submitted`, remind the user that the plugin never submits anything (FR-036): paste the texts into the conference site yourself, for example from `/cfp:draft --proposal <id>` which prints the paste view, then record the date here.
4. On `"ok": false`:
   - Error contains `allowed targets`: explain the current status and the allowed targets from the message. When targets exist, ask (AskUserQuestion) which target to apply, with `none` as an option; rerun with the chosen target or stop.
   - Error contains `not ready` (only for `--to ready`): list the reasons from the message. Explain that automatic ready needs a passing committee review and a clean pre-flight (FR-031a). Offer (AskUserQuestion) `force ready` (manual ready, FR-031a), `run /cfp:check first`, or `stop`. On force, rerun with `--force` and show the resulting side effect. On check, invoke the `cfp:check` skill with the proposal id, then ask again.
   - Error contains `date must be ISO`: ask for the date again in `YYYY-MM-DD`.
   - Anything else: show the error and stop.

## `reopen <id> [--event <id>]`

1. Run `proposal show --proposal "<id>"`. On error show it, run `proposal list`, and ask which proposal to reopen.
2. Check `status`. If it is not `rejected` or `withdrawn`, warn that reopening is meant for rejected or withdrawn proposals and ask (AskUserQuestion) whether to continue anyway; on no, stop.
3. Show the reference material from the source: `fields.title`, `fields.abstract`, and the reviewer-only relevance text (`fields.benefits` when present, otherwise the field whose profile definition has `audience: reviewer`; run `profile show --profile <profile> --event <event>` to find it when needed). Also mention the source `talk` id and that the talk story is reused as is.
4. Target event. When `--event` is given, use it. Otherwise run `profile list` and ask (AskUserQuestion) which event to target: offer the events of the source proposal's `profile` that are not the source event (show `cfp_close` and `days_to_close`, mark closed ones), plus `another profile` (then ask for the profile and its event). When the chosen profile has no suitable event, say that `/cfp:draft` offers inline event creation and continue with the profile only.
5. Invoke the `cfp:draft` skill via the Skill tool with the arguments `--talk <source talk> --profile <profile> --event <target event>` (omit `--event` when none was chosen). Tell it in the invocation message that this is a reopen of proposal `<id>`, that the old title, abstract, and reviewer-only text shown above are available for reference while drafting, and that the source proposal keeps its status (FR-035). Do not change the source proposal.
6. After the draft skill returns, remind the user that the source proposal is still `<status>` and that the repeat rule treats a rejected proposal as not presented.
