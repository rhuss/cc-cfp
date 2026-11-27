---
name: cfp:draft
description: This skill should be used when the user runs "/cfp:draft", asks to "draft a proposal", "write a KubeCon abstract", "start a CFP submission", "resume my proposal", "turn this idea into a talk proposal", or wants to continue an unfinished draft. Interactive twelve-step flow from story interview to paste view, saving through the store CLI at every step.
argument-hint: "[--profile <id>] [--event <id>] [--talk <id>] [--proposal <id>] [--from <path or URL>]"
allowed-tools: ["Bash", "Read", "Write", "AskUserQuestion", "Skill", "Agent", "WebFetch"]
---

# cfp:draft

Draft a proposal from an idea, existing material, a stored talk, or an old proposal, then review, voice, pre-flight, and render it. Follow Step 0 and the shared rules in `skills/_shared/preamble.md` under `PLUGIN_ROOT`: one question at a time, show every generated text with its count before saving, never edit store files directly, no em-dash or en-dash in generated prose, nothing is ever submitted.

Every CLI call below is `python3 -I "$PLUGIN_ROOT/scripts/cfp_store.py" <group> <sub> ...`. Long texts are written to the session scratchpad first and passed with `--text-file` or `--from-json`.

## Step 0: Context and config

Run Step 0 from the preamble. Then read the configuration:

```bash
python3 -I "$PLUGIN_ROOT/scripts/cfp_store.py" config show
```

Keep `speaker_name`, `speaker_company`, `voice_profile`, `review_rounds`, and `default_profile` for the steps below. Parse `$ARGUMENTS` for `--profile`, `--event`, `--talk`, `--proposal`, `--from`.

### Resume

With `--proposal <id>`: run `proposal show --proposal <id>`, work out the first incomplete step (see "Resuming" at the end), tell the user where the draft stands, and continue from there.

Without `--proposal`: run `proposal list --status draft`. When drafts exist, ask (AskUserQuestion) whether to resume one of them (list id, title, event, updated) or start new. On resume, load it with `proposal show` and continue as above. On new, go to Step 1.

## Step 1: Profile and event

```bash
python3 -I "$PLUGIN_ROOT/scripts/cfp_store.py" profile list
```

Offer the profiles with `default_profile` first (skip the question when `--profile` was given or only one profile exists). Then offer the profile's events with their names and `days_to_close` from `event list --profile <id>`. Skip when `--event` was given.

Missing event (FR-010a): when the user's target edition is not in the list, offer two ways to create it inline, then continue drafting:

- Research: invoke the `cfp:profile` skill with `refresh <profile> --event <id or URL>`. It writes the override with `approved: false` and asks for approval section by section.
- Manual entry: ask one at a time for name, location, event start and end dates, CFP open and close dates, notification date, tracks (as a list), and submission limit. Write `{"id", "profile", "name", "location", "event_start", "event_end", "cfp_open", "cfp_close", "notification", "tracks", "submission_limit", "approved": true}` to a scratchpad file and run `event write --profile <id> --event <id> --from-json <file>`. Manual entry counts as approved (FR-009).

Then load the effective profile:

```bash
python3 -I "$PLUGIN_ROOT/scripts/cfp_store.py" profile show --profile <id> --event <event-id>
```

Refuse to continue when `approved` is false; point to `/cfp:profile show <id>` and `/cfp:profile refresh <id> --event <event-id>` for the approval step. Warn when `cfp_close` is before `<today>` (the deadline has passed; drafting continues for a future edition or as practice).

## Step 2: Session type

List `session_types` from the effective profile with name, `duration_min`, and `min_speakers` to `max_speakers`. Ask the user to pick one.

When the chosen type has `min_speakers` above 1: say that the solo speaker cannot satisfy it and ask whether co-speakers exist. On no, go back to the list. On yes, ask for each co-speaker as "Name, Company" (one question per speaker, until the user says done or `max_speakers` minus 1 is reached), then optionally for their genders (needed by the all-men rule; "unknown" is allowed and counts as unknown, not as a non-man). Keep both lists for Step 4b, where they are stored through a JSON file: `{"co_speakers": [...], "co_speaker_genders": [...]}` written to `<scratchpad>/cfp-meta.json` and passed with `proposal set-meta --proposal <id> --from-json <file>`.

## Step 3: Input source

Ask which input to start from (skip when `--from` or `--talk` was given):

1. One-line idea: ask for it and continue with Step 4.
2. Existing material (`--from <path or URL>`): Read a local file; WebFetch a public URL (never a login-walled page). Extract problem, contribution, takeaways, personas, projects, and anything about prior outings into a pre-filled story, show the pre-fill, and ask only for the gaps in Step 4.
3. Existing talk: `talk list`, pick one, `talk show --talk <id>`, continue with Step 4 against the gaps.
4. Existing proposal: `proposal list`, pick one, `proposal show`. Use its `talk`, show its old title, abstract, and reviewer-only text for reference (read only, never copied blindly). A source proposal with status rejected or withdrawn is not a presentation: do not add an outing of kind `presented` for it.

## Step 4: Story interview

Create or update the talk from the pre-fill as soon as there is a title:

```bash
python3 -I "$PLUGIN_ROOT/scripts/cfp_store.py" talk write [--talk <id>] --from-json <scratchpad>/cfp-talk.json
```

The JSON carries `title`, `personas`, `projects`, `outings`, `resources`, `source_material`, and `sections` with the keys `Problem`, `Contribution`, `Takeaways`, `What is new`, and `Story notes`. Keep the returned `id`.

Then loop:

```bash
python3 -I "$PLUGIN_ROOT/scripts/cfp_store.py" talk complete --talk <id>
```

For each entry in `missing` ask one question about that section (Problem: what hurts and for whom; Contribution: what the speaker built, changed, or measured; Takeaways: three concrete things an attendee can do afterwards; What is new: compared with existing talks and docs; Story notes: the hard parts, surprises, open questions). For each entry in `missing_meta` ask for that list (personas as roles, projects by exact name). Save with `talk write` after every answer, then re-run `talk complete` until `complete` is true.

Also ask once about prior outings of the same material (event, date, link, kind `presented` or `submitted`; family is the profile id when the event belongs to this conference family) and once whether to link stored resources: run `resource list` and offer them. Save both on the talk.

## Step 4b: Create the proposal

```bash
python3 -I "$PLUGIN_ROOT/scripts/cfp_store.py" proposal create --talk <talk-id> --profile <id> --event <event-id> --session-type <type-id>
```

When the error says a proposal for this talk and event already exists, resume that proposal instead of failing. Store co-speakers from Step 2 with `proposal set-meta`. From here on every step saves to this proposal id.

## Step 5: Angles

Follow `$PLUGIN_ROOT/knowledge-base/guidance/abstract-angles.md` (problem-first, story-driven, contrarian; the two-sentence value rule; the abstract structure; how to present candidates). Use the profile's `title` and `abstract` field guidance and limits, the speaker name in third person, and the talk sections.

Present two or three candidates in one message, each with its label, the title with its character count against the title limit, the abstract with its count against the abstract limit, and a one-line note on the hook. Ask the user to pick one or request another round (ask what to change first, replace only rejected candidates).

Save the choice (the angle label is free text, so it goes through a JSON file `{"angle": "<label>"}`):

```bash
python3 -I "$PLUGIN_ROOT/scripts/cfp_store.py" proposal set-meta --proposal <id> --from-json <scratchpad>/cfp-meta.json
python3 -I "$PLUGIN_ROOT/scripts/cfp_store.py" proposal set-field --proposal <id> --field title --text-file <scratchpad>/cfp-title.txt
python3 -I "$PLUGIN_ROOT/scripts/cfp_store.py" proposal set-field --proposal <id> --field abstract --text-file <scratchpad>/cfp-abstract.txt
```

## Step 6: Field drafting

Iterate `fields` from `profile show` in order. Skip `title` and `abstract` when already saved. For every field use its `guidance`, `limit`, `limit_status`, and `options`. For every generated field the message sequence is fixed: (1) a heading with the field label, (2) the complete drafted text in a fenced block, (3) the line `<chars>/<limit> chars` (approximate when unverified), (4) one AskUserQuestion with `save`, `change something`, `regenerate`. Never replace step 2 with a summary of what the text contains. After each save show `chars/limit` and the returned `status`; when `status` is `over`, offer to shorten right away, show the shortened text the same way, and save again. Label unverified limits as approximate.

Per field kind:

- `choice` and `boolean`: ask with AskUserQuestion, never generate. Track options come from the event's `tracks` list; audience level from the field `options`; `format` defaults to the chosen session type's name. Save choice fields with `proposal set-field --text-file`; for `track` and `audience_level` this one call also updates the front matter that pre-flight reads (no second `set-meta` call needed). Track names come from fetched pages, so they always travel through the text file, never as a shell argument.
- Reviewer-only relevance field: the one field whose id is `relevance_field` in the `profile show` output (`value_to_community` on the current KubeCon form, `benefits` on older ones; null when the form has none). Draft it per `$PLUGIN_ROOT/knowledge-base/guidance/benefits-field.md` (who benefits by persona, why now, what is new, credentials and evidence, data shown; never restate the abstract). Run its checklist before showing the text. Every other reviewer-only text field is drafted from its own `guidance`, like the other text fields below.
- `previously_presented`: build from the talk outings. With a `presented` outing inside the conference family in the last twelve months, describe the significant differences (new data, scope, results) and mention a link to slides or video. Otherwise state plainly that the talk has not been presented before.
- Project list fields (`cncf_oss_projects` on the current KubeCon form, or `cncf_projects` and `open_source_projects` on older profiles): build from the talk `projects`; print the proposed list in a fenced block exactly as it will be saved (one project per line with its link where known), then ask the user to confirm or correct names and links.
- Resources field (the field with id `resources`, whether its kind is `resources` or free text such as `longtext`): run `resource list`, offer recordings first and recommend one (FR-027: the Speaker criterion reaches its top level only with a recording). Let the user pick, up to the form's maximum when the field guidance names one, then save with `proposal set-meta --proposal <id> --resources id,id`. That call stores the ids and writes one `Title: link` line per resource into the field. On a free-text field, print the resulting lines in a fenced block and ask whether to add what the field guidance asks for beyond the stored resources (for example recordings of co-speakers); when the user adds something, save the complete text with `proposal set-field --proposal <id> --field resources --text-file <file>`. When no recording exists, say so and suggest `/cfp:bio resource add` later.
- Other `text` and `longtext` fields: draft per guidance, print the full text in a fenced block with its count, ask, save.

Bio: when `bio_on_form` is false in the `profile show` output, the form has no speaker bio. Say so in one line, attach none, and skip the rest of this bio part. Otherwise run `bio list`. Show each variation with `chars` against `bio_limit` (`bio_limit_status` tells whether the limit is verified). Ask which one to use. Before attaching the chosen variation, run `bio show --name <name>` and print its complete text in a fenced block with `<chars>/<bio_limit> chars`, then ask to attach, shorten, or pick another. When the bio is drafted fresh inside this flow (no stored variation fits), the same rule applies: the complete bio text appears in a fenced block above the question that offers to save it. Then:

```bash
python3 -I "$PLUGIN_ROOT/scripts/cfp_store.py" proposal set-meta --proposal <id> --bio "<name>"
```

When the chosen bio is over the limit, offer to shorten it. Print the shortened text in full in a fenced block with its count, ask, then write it to a file and run `proposal set-bio-text --proposal <id> --text-file <file>`. This changes only the proposal's snapshot; the stored variation stays untouched (FR-026). When no bios exist, offer to run the `cfp:bio` skill with `new` and continue afterwards.

Every field goes through:

```bash
python3 -I "$PLUGIN_ROOT/scripts/cfp_store.py" proposal set-field --proposal <id> --field <field-id> --text-file <scratchpad>/cfp-field-<field-id>.txt
```

## Step 7: Committee review loop

Set `round = 0`. Loop:

1. Invoke the `cfp:committee-review` skill with `--proposal <id>`. It builds the packet, spawns the `cfp:committee-reviewer` agent, records the round, and returns the computed verdict, `below_min`, and suggestions. Increment `round`.
2. Verdict `pass`: continue with Step 8.
3. Verdict `none` (the agent reply could not be validated twice): report it and offer to retry the round or park the proposal.
4. Verdict `revise`: show the suggestions and ask which to apply (all, a subset by number, or none). For each accepted suggestion, rewrite that field following the instruction and the field guidance, show the new text with its count, and save it with `proposal set-field` (or `proposal set-bio-text` for the bio). When the user applies none, ask whether to run another round anyway or stop.
5. When `round` is below `review_rounds`, go back to 1.

When `round` reaches `review_rounds` without a pass: list the remaining weaknesses (criteria in `below_min` with their last comments, and open suggestions) and ask (AskUserQuestion) one of:

- Continue: one more round, then ask again.
- Accept as is: continue with Step 8 without a pass. Say that the proposal will stay in `draft` because `ready` requires a passing verdict; the user can submit it anyway and record the status with `/cfp:status`.
- Park: stop here. Everything is saved as draft; `/cfp:draft --proposal <id>` resumes.

## Step 8: Voice pass

Only after a pass verdict (FR-021). Skip silently to Step 9 when the last verdict is not `pass`.

For each of: `title`, `abstract`, the reviewer-only relevance field (the id in `relevance_field` from `profile show`, when it is not null), and the bio snapshot (from `proposal show`; only when `bio_on_form` is true), invoke the `prose:humanizer` skill through the Skill tool with the text and `voice_profile` from the config (omit the voice when empty). Then:

- Skill tool reports the skill as unavailable: print "Voice pass skipped: prose plugin not installed" and go to Step 9. Texts stay as drafted.
- Skill returns usage or help text instead of a rewrite: apply the humanizer core rules inline (no AI vocabulary, no rule-of-three padding, no inflated symbolism, varied sentence length, no em-dash or en-dash) and tell the user the rewrite was done inline.
- Skill returns a rewrite: print the full rewritten text in a fenced block with its count against the limit, then ask whether to keep it or the previous version. Keep the title's meaning; it is rewritten only for wording.

Save each rewritten text with `proposal set-field` (or `proposal set-bio-text` for the bio), then:

```bash
python3 -I "$PLUGIN_ROOT/scripts/cfp_store.py" count --proposal <id>
python3 -I "$PLUGIN_ROOT/scripts/cfp_store.py" proposal mark-voice-pass --proposal <id>
```

No second committee review after the voice pass.

## Step 9: Over-limit shortening

From the `count` output, for every id in `over` (and the bio when its status is `over`): show the current count and limit, offer to shorten, show the shortened text with its count, save, and recount. Repeat until `over` is empty or the user declines for a field. Declined fields stay flagged in the paste view.

## Step 10: Pre-flight

```bash
python3 -I "$PLUGIN_ROOT/scripts/cfp_store.py" preflight --proposal <id> --today <today>
```

`passed` is the rule verdict; the top-level `ok` only says the call succeeded. `manual` lists the rules the CLI cannot compute, each with its `severity`, `params`, `text`, and `source`.

Then make the two checks that need judgement. Read `$PLUGIN_ROOT/skills/_shared/preflight-checks.md` and follow it: the audience level comparison (FR-029) against the levels this profile's form offers, and every rule of kind `custom` in `manual`, judged against the proposal. Use the `count` result from Step 8 or 9, and run `count` again when a field changed since. Each finding is written to `<scratchpad>/cfp-finding.json` and recorded with:

```bash
python3 -I "$PLUGIN_ROOT/scripts/cfp_store.py" preflight add-finding --proposal <id> --from-json <scratchpad>/cfp-finding.json
```

A violated custom rule takes its severity from the profile, so a `disqualify` rule blocks `ready` like a computed one. Every `preflight` run drops these findings; make both checks again after each re-run.

Show every finding with its severity (`disqualify` or `warn`), text, and `source`, then one line per custom rule with its verdict, then the `vendor_pitch` rules the committee review covers, then any `problems` (proposal files that could not be read; the submission count may be low). Then handle:

- Track finding: show the event's track list and let the user pick; save with `proposal set-field --field track --text-file <file>` (this also updates the front matter), then re-run `preflight`.
- Repeat warning: ask whether the `previously_presented` text explains significant differences; offer to rewrite that field when it does not, then re-run.
- Audience level warning: offer to change the level (`proposal set-field --field audience_level`) or the abstract, then re-run.
- Violated custom rule: explain the rule. When a field causes it (a style rule, a required field that is still empty), offer to rewrite or draft that field, then re-run. Otherwise say what would resolve it outside this field set.
- Other disqualifying findings (submission limit, speaker count, panel rules): explain the rule and what would resolve it; these need changes outside this field set.

Any `set-field`, `set-bio-text`, or `set-meta` call on a proposal that is already `ready` moves it back to `draft` (the result carries `reset_to_draft: true`); say so and continue with the review and pre-flight again.

## Step 11: Ready

```bash
python3 -I "$PLUGIN_ROOT/scripts/cfp_store.py" status ready-check --proposal <id>
```

When `can_ready` is true, run `status set --proposal <id> --to ready` and report it. Otherwise list `reasons` (no passing review, disqualifying pre-flight finding) and say the proposal stays in draft; `/cfp:status set <id> ready` can force it later.

## Step 12: Paste view

```bash
python3 -I "$PLUGIN_ROOT/scripts/cfp_store.py" pasteview --proposal <id> --format markdown
```

Print the output in full (it is markdown, not JSON), then the proposal path from `proposal show`, then one line reminding the user that nothing was submitted: paste the fields into the conference form and record the submission with `/cfp:status set <id> submitted`.

## Resuming

Resume detection reads `proposal show` and picks the first step whose data is missing:

- No `title` or `abstract` field: Step 5 (after checking `talk complete`, which may send the flow back to Step 4).
- A required field from `profile show` is missing, or `bio` is empty while `bio_on_form` is true: Step 6 for the missing parts only.
- `review_rounds` is empty, `review_stale` is true (the proposal was `ready` and was then edited or moved back to `draft`, so the last review no longer covers its text; edits to a draft, such as the voice pass and shortening, do not set it), or the last verdict is `revise` and the round count is below `review_rounds` from the config: Step 7.
- Last verdict `pass` and `voice_pass` false: Step 8.
- `count` reports entries in `over`: Step 9.
- `preflight` is empty or its `date` is older than the proposal's `updated`: Step 10.
- Status `draft` with a passing review and `preflight.ok` true: Step 11.
- Everything else: Step 12.

Tell the user which step the draft resumes at and why before asking the next question.

## Related skills

- `cfp:committee-review`: one review round on a stored proposal (used in Step 7).
- `cfp:bio`: bio variations and speaker resources used in Step 6.
- `cfp:profile`: research, refresh, and approve profiles and event overrides (Step 1).
- `cfp:check`: standalone pre-flight on any proposal (same rules as Step 10).
- `cfp:status`: lifecycle changes after submission, listing, and reopening a rejected proposal for a new event.
