---
name: cfp:committee-review
description: This skill should be used when the user asks to "review my proposal", "run the committee review", "score this proposal", "simulate the program committee", or when the cfp:draft skill reaches its review step. Builds the review packet, spawns the committee-reviewer agent, validates its JSON, records the round, and reports scores, verdict, and suggestions.
argument-hint: "--proposal <id> [--examples <n>]"
allowed-tools: ["Bash", "Read", "Write", "Agent"]
---

# cfp:committee-review

Run one simulated program committee round on a stored proposal. Follow Step 0 and the shared rules in `skills/_shared/preamble.md` under `PLUGIN_ROOT`.

Arguments: `--proposal <id>` (required; when missing, run `proposal list` and ask which one) and `--examples <n>` (optional, number of calibration examples in the packet, default 3).

The verdict reported at the end comes from `review record`, which applies the profile's thresholds to the scores. The agent's own `verdict` field is advisory and is stored with the round but never decides the outcome.

## Step 1: Build the packet

```bash
python3 -I "$PLUGIN_ROOT/scripts/cfp_store.py" review packet --proposal "<id>" --examples <n>
```

On `"ok": false`, show the error and stop (typical causes: unknown proposal id, no drafted fields yet).

Write the `packet` object from the output, as JSON, to `<scratchpad>/cfp-review-packet-<id>.json` with the Write tool. The scratchpad is the session scratchpad directory named in the environment, never `/tmp`.

## Step 2: Spawn the reviewer

Use the Agent tool with `subagent_type: "cfp:committee-reviewer"`. The prompt is short and contains only:

- The absolute path of the packet file.
- The instruction to read only that file.
- The instruction to reply with exactly one JSON object matching the schema in the agent definition, with no prose and no code fence.

Do not paste the drafted fields, the rubric, or any drafting history into the prompt. The agent must form its opinion from the packet alone.

## Step 3: Extract and validate the JSON

The agent may wrap the object in prose or a code fence despite the instruction. Take the first `{` ... `}` block that parses as JSON. Then check:

1. `scores` is a map with exactly the criterion ids from `packet.rubric.criteria`; every value is a number from 0 to `packet.rubric.scale_max` in whole or half steps.
2. `comments` is a map with the same criterion ids; every value is a non-empty string.
3. `verdict` is `"pass"` or `"revise"`.
4. `suggestions` is a list (may be empty) of objects with a `field` string that is an id in `packet.fields` and a non-empty `text` string.

When any check fails, or no JSON object can be parsed, spawn the agent once more. Quote the exact validation problem in the second prompt (for example: "Your previous reply had no score for criterion speaker" or "The reply was not parseable JSON"), together with the packet path and the same output instruction.

When the second reply fails validation too, end the round: tell the user that the committee review could not be recorded, name the problem (missing criterion, out-of-range score, unparseable reply), and stop. Do not run `review record` and do not invent scores. Return `verdict: none` to the caller.

## Step 4: Record the round

Write the validated JSON to `<scratchpad>/cfp-review-result-<id>.json` and run:

```bash
python3 -I "$PLUGIN_ROOT/scripts/cfp_store.py" review record --proposal "<id>" --from-json "<scratchpad>/cfp-review-result-<id>.json"
```

The output has `round`, `verdict` (computed from the thresholds), `average`, `below_min` (criteria under the minimum), and `suggestions`. On `"ok": false`, show the error and stop.

## Step 5: Present the result

Print a compact table, one row per criterion, in the order of `packet.rubric.criteria`:

| Criterion | Score | Comment |
|---|---|---|
| Content | 3.5 / 5 | ... |

Below the table:

- Round number and verdict from `review record` (not the agent's field). Say "Verdict: pass" or "Verdict: revise".
- Average against `pass_average`, and the list of criteria in `below_min` against `pass_min_criterion`. When the list is empty, say so.
- The suggestions as a numbered list, each prefixed with its field id in backticks.

When the agent's advisory verdict differs from the computed one, add one line noting it.

## Step 6: Return to the caller

When invoked from `cfp:draft`, return the computed verdict (`pass`, `revise`, or `none`), the round number, the `below_min` list, and the suggestions list unchanged, so the draft skill can offer the rewrites. When invoked directly by the user, end with a hint: `/cfp:draft --proposal <id>` continues the drafting flow with these suggestions.

## Related skills

- `cfp:draft` runs this skill in its review loop, bounded by `review_rounds` from the config.
- `cfp:check` runs the pre-flight rules, which the committee does not evaluate.
