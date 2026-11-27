# Pre-flight checks that need judgement

`preflight --proposal <id>` computes the rules it can decide from the store: submission limit, repeat within months, track, speaker count, and the panel rules. Two checks need judgement, and the skill that ran `preflight` makes them: the audience level comparison and the profile's `custom` rules. `cfp:check` and `cfp:draft` both follow this file, so a proposal gets the same verdict from either.

## How findings are recorded

Every `preflight` run replaces the stored findings. Run both checks below again after each run and add back what still applies.

A finding goes through a JSON file, because free text never goes on the command line:

```bash
python3 -I "$PLUGIN_ROOT/scripts/cfp_store.py" preflight add-finding \
  --proposal "<id>" --from-json "<scratchpad>/cfp-finding.json"
```

The call returns the updated `passed` and `findings`. Use the result of the last call for the report. `passed` is false as soon as one finding has the severity `disqualify`, and such a proposal cannot become `ready`.

## What to load

Both checks read stored data only:

- `proposal show --proposal <id>`: the fields, `session_type`, `track`, `audience_level`, `co_speakers`.
- `profile show --profile <profile> --event <event>`: the field definitions (`options`, `guidance`) and the session types.
- `count --proposal <id>`: `missing_required` and `over`.
- `config show`: `speaker_name` and `speaker_company`.

Reuse results the calling skill already has. Run a command only when its result is missing or older than the last edit.

## Audience level comparison (FR-029)

Compare the abstract with the level the proposal claims, in the words of this conference's form.

1. The stored level is `audience_level` from `proposal show`. The levels the form offers are the `options` of the `audience_level` field in `profile show`, in form order. They differ between conferences: KubeCon offers `Any`, `Beginner`, `Intermediate`, `Advanced`, while another form may offer `Technical, introductory` or `Non-technical, business-focused`. When the field's `guidance` defines the levels, use those definitions.
2. Skip the comparison and say so in one line when the abstract or the level is empty, or when the profile has no `audience_level` field.
3. Decide which offered level the abstract really serves. Look at what it assumes (terminology it does not explain, internals, prior hands-on experience) and at what it promises (a first look with definitions, or depth).
4. It is a mismatch only when another offered level clearly fits better than the stored one. Typical cases: material that needs deep prior knowledge (scheduler internals, eBPF probes, custom controllers, kernel paths) under an entry-level option; a definitions-first introduction under the most advanced option; a middle level when the abstract clearly belongs to one of the two ends. A level that means "any audience" fits unless the abstract needs specialist knowledge. When in doubt, there is no mismatch.
5. On a mismatch, write `{"rule": "audience-level", "severity": "warn", "text": "<one sentence: what the abstract assumes or promises, and which offered level fits better>"}` to the JSON file and add it. Name the better level exactly as the form words it. When the level fits, say so in one line and add nothing.

## Custom rules

Rules of kind `custom` hold conference rules that have no evaluator of their own. `preflight` returns them in `manual`, each with `rule` (its id), `severity`, `params`, `text`, and `source`. Judge every one against the proposal.

1. Read the rule `text` as the conference wrote it. `params` narrows it: a rule with `params.session_type` applies only to proposals of that session type, and other params (for example `min`) are the numbers the text talks about.
2. Reach one verdict per rule from the stored data listed above:
   - `violated`: the stored data shows that the proposal breaks the rule. A rule about incomplete proposals is violated while `missing_required` is not empty. A style rule is violated when a drafted field shows what it forbids.
   - `met`: the stored data shows that the proposal satisfies the rule.
   - `does not apply`: the rule is about a session type or a situation this proposal is not in.
   - `cannot tell`: the rule depends on something the store does not hold, for example whether a co-speaker agreed to travel.
3. `violated`: write `{"rule": "<rule id>", "text": "<one sentence that names what breaks the rule>"}` to the JSON file and add it. Leave out `severity` and `source`. The CLI takes both from the profile rule, so a `disqualify` rule blocks `ready` and a `warn` rule does not.
4. `cannot tell` on a `disqualify` rule: quote the rule text and ask (AskUserQuestion) whether the proposal meets it, with the options `yes`, `no`, and `not sure`. On `no`, add the finding as in 3. On `not sure`, add it with `"severity": "warn"` and a text that says the rule could not be confirmed. On `yes`, add nothing.
5. `cannot tell` on a `warn` rule: add nothing. List the rule in the report as one the user has to confirm.
6. `met` and `does not apply`: add nothing.

Rules of kind `vendor_pitch` stay with the committee review. List them as manual and add no finding.

## What to report

After both checks, the calling skill shows:

- every finding with its severity, text, and source, `disqualify` first;
- one line per custom rule with its verdict (`violated`, `met`, `does not apply`, `confirm yourself`), so the user sees what was checked;
- the `vendor_pitch` rules as "judged by the committee review".
