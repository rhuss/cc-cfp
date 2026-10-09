---
name: cfp:check
description: This skill should be used when the user runs "/cfp:check", asks to "run the pre-flight check", "check a proposal before submission", "check the hard rules", "verify the submission limit", "check the track", "check the audience level", or "count the characters of a proposal". Runs the profile's hard rules, the audience-level comparison, and the character counts on a stored proposal and reports findings with severity and source.
argument-hint: "<proposal-id>"
allowed-tools: ["Bash", "Read", "AskUserQuestion", "Skill"]
---

# cfp:check

Standalone pre-flight check on any stored proposal (FR-028a). Follow Step 0 and the shared rules in `skills/_shared/preamble.md` under `PLUGIN_ROOT`. Pass `--today "<today>"` to `preflight`.

## Step 1: Pick the proposal

Take the proposal id from `$ARGUMENTS`. When absent, run `proposal list`, show a table (id, title, event, status), report `problems` once, and ask (AskUserQuestion) which proposal to check. Prefer offering draft and ready proposals first; the check works on any status.

## Step 2: Load the proposal

Run `proposal show --proposal "<id>"`. Keep `fields.abstract`, `audience_level`, `track`, `profile`, `event`, and `session_type`. On error show it and stop.

## Step 3: Run the rules

```bash
python3 -I "$PLUGIN_ROOT/scripts/cfp_store.py" preflight --proposal "<id>" --today "<today>"
```

The result has `passed` (the rule verdict: true when no `disqualify` finding exists), `findings`, `manual`, and `problems` (proposal files that could not be parsed and were not counted toward the submission limit; report them once). The top-level `ok` only says the call succeeded. The result replaces the proposal's stored pre-flight map, so an earlier audience-level finding is gone and must be re-added in Step 4 when it still applies.

## Step 4: Audience level comparison (FR-029)

Compare `fields.abstract` against `audience_level` yourself. Flag a mismatch when:

- the abstract relies on advanced terminology, internals, or prior hands-on experience (for example scheduler internals, eBPF probes, custom controllers, operator reconciliation details) but the level is `Beginner` or `Any`, or
- the abstract is introductory (defines basic terms, promises a first look or an overview) but the level is `Advanced`, or
- the level is `Intermediate` and the abstract clearly belongs to one of the two ends above.

Skip the comparison when the abstract or the level is empty and say so. When they disagree, write a one-sentence reason as `{"rule": "audience-level", "severity": "warn", "text": "<reason>"}` to `<scratchpad>/cfp-finding.json` (free text never goes on the command line) and run:

```bash
python3 -I "$PLUGIN_ROOT/scripts/cfp_store.py" preflight add-finding \
  --proposal "<id>" --from-json "<scratchpad>/cfp-finding.json"
```

Use the returned `passed` and `findings` from this call for the report. When they agree, state that in one line.

## Step 5: Counts

Run `count --proposal "<id>"`. Keep `fields`, `bio`, `over`, and `missing_required`.

## Step 6: Report

Print, in this order:

1. **Findings** (FR-030):

| Rule | Severity | Finding | Source |
|---|---|---|---|

Write `disqualify` or `warn` in the Severity column and sort disqualify first. Show `source` as given (URL or profile reference); write `profile` when empty. When there are no findings, print "No rule findings."

2. **Manual rules** from `manual`: a short table (rule, text, source) with the note that only the committee review can judge these (for example vendor pitch).

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
- `fix the track` (offer only when a `track_in_event` finding exists): run `profile show --profile <profile> --event <event>`, list `tracks`, ask which to use, write the chosen name to `<scratchpad>/cfp-track.txt` and run `proposal set-field --proposal "<id>" --field track --text-file <file>` (this also updates the front matter), then rerun from Step 3.
- `change the audience level` (offer only when an `audience-level` finding exists): offer the levels from the profile's audience field options, write the choice to a text file and run `proposal set-field --proposal "<id>" --field audience_level --text-file <file>`, then rerun from Step 3.

A `set-field` on a proposal that is already `ready` moves it back to `draft` (`reset_to_draft: true` in the result); mention it.
- `done`: stop.

For a `repeat_within_months` warning, mention that a previously-presented note in the proposal explaining significant differences turns the rule into a warning, and that the note is edited through `/cfp:draft --proposal <id>`.
