---
name: cfp:check
description: This skill should be used when the user runs "/cfp:check", asks to "run the pre-flight check", "check a proposal before submission", "check the hard rules", "verify the submission limit", "check the track", "check the audience level", or "count the characters of a proposal". Runs the profile's hard rules, judges its custom rules and the audience level against the proposal, counts the characters, and reports findings with severity and source.
argument-hint: "<proposal-id>"
allowed-tools: ["Bash", "Read", "Write", "AskUserQuestion", "Skill"]
---

# cfp:check

Standalone pre-flight check on any stored proposal (FR-028a). Follow Step 0 and the shared rules in `skills/_shared/preamble.md` under `PLUGIN_ROOT`. Pass `--today "<today>"` to `preflight`.

## Step 1: Pick the proposal

Take the proposal id from `$ARGUMENTS`. When absent, run `proposal list`, show a table (id, title, event, status), report `problems` once, and ask (AskUserQuestion) which proposal to check. Prefer offering draft and ready proposals first; the check works on any status.

## Step 2: Load the proposal and its profile

Run `proposal show --proposal "<id>"`. Keep `fields`, `audience_level`, `track`, `profile`, `event`, `session_type`, and `co_speakers`. On error show it and stop.

Run `profile show --profile <profile> --event <event>`. Keep `fields` (with their `options` and `guidance`) and `session_types`. Steps 5 and 7 need them.

## Step 3: Run the rules

```bash
python3 -I "$PLUGIN_ROOT/scripts/cfp_store.py" preflight --proposal "<id>" --today "<today>"
```

The result has `passed` (the rule verdict: true when no `disqualify` finding exists), `findings`, `manual`, and `problems` (proposal files that could not be parsed and were not counted toward the submission limit; report them once). The top-level `ok` only says the call succeeded. `manual` lists the rules the CLI cannot compute, each with `rule`, `kind`, `severity`, `params`, `text`, and `source`.

The result replaces the proposal's stored pre-flight map. Findings added by an earlier Step 5 (audience level, custom rules) are gone and are added again in Step 5 when they still apply.

## Step 4: Counts

Run `count --proposal "<id>"`. Keep `fields`, `bio`, `over`, and `missing_required`. When `bio.on_form` is false, the form has no speaker bio: leave the bio out of the report.

## Step 5: Checks that need judgement

Read `skills/_shared/preflight-checks.md` under `PLUGIN_ROOT` and follow it:

1. The audience level comparison (FR-029), against the levels this profile's form offers.
2. Every rule of kind `custom` in `manual`, judged against the proposal. Run `config show` when a rule needs the speaker name or company.

Each finding is written to `<scratchpad>/cfp-finding.json` with the Write tool and recorded with `preflight add-finding --proposal "<id>" --from-json <file>`. Take `passed` and `findings` for the report from the last `add-finding` call, or from Step 3 when nothing was added.

## Step 6: Report

Print, in this order:

1. **Findings** (FR-030):

| Rule | Severity | Finding | Source |
|---|---|---|---|

Write `disqualify` or `warn` in the Severity column and sort disqualify first. Show `source` as given (URL or profile reference); write `profile` when empty. When there are no findings, print "No rule findings."

2. **Judged and manual rules** from `manual`:

| Rule | Severity | Verdict | Rule text |
|---|---|---|---|

The verdict of a `custom` rule is the one from Step 5: `violated` (it is also in the findings table), `met`, `does not apply`, or `confirm yourself` (the store does not hold what the rule needs). For a `vendor_pitch` rule write `committee review`: only the committee review can judge it.

3. **Over-limit fields** from `over`: for each id show `label`, `chars/limit`, and `limit_status`. When `bio.status` is `over`, include the bio.

4. **Missing required fields** from `missing_required` with their labels.

5. **Unverified limits**: when any counted field or the bio has `limit_status: unverified`, add one line saying those limits are approximate and the live form may differ.

6. **Verdict**: one of
   - "Passed: no disqualifying findings" when `passed` is true (list remaining warnings in one sentence), or
   - "Failed: N disqualifying finding(s)" when false.

   Then run `status ready-check --proposal "<id>"` and report `can_ready` with its `reasons` ("Can become ready" or "Cannot become ready automatically: ..."). For a proposal already past draft, say the check is informational.

## Step 7: Offer fixes

Ask (AskUserQuestion) what to do next:

- `open the draft flow`: invoke the `cfp:draft` skill with `--proposal <id>` so the user can fix the flagged fields; when the Skill tool is not available in this session, print `/cfp:draft --proposal <id>` for the user to run and stop.
- `fix the track` (offer only when a `track_in_event` finding exists): list `tracks` from the `profile show` output, ask which to use, write the chosen name to `<scratchpad>/cfp-track.txt` and run `proposal set-field --proposal "<id>" --field track --text-file <file>` (this also updates the front matter), then rerun from Step 3.
- `change the audience level` (offer only when an `audience-level` finding exists): offer the `options` of the profile's `audience_level` field, write the choice to a text file and run `proposal set-field --proposal "<id>" --field audience_level --text-file <file>`, then rerun from Step 3.
- `done`: stop.

A `set-field` on a proposal that is already `ready` moves it back to `draft` (`reset_to_draft: true` in the result); mention it.

For a `repeat_within_months` warning, mention that a previously-presented note in the proposal explaining significant differences turns the rule into a warning, and that the note is edited through `/cfp:draft --proposal <id>`. A violated custom rule is fixed in the draft flow too, or outside cfp when it is about speakers or the session type.
