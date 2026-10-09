# Contract: Slash Commands

All commands live under `/cfp:` and are thin wrappers that invoke the skill of the same name with `$ARGUMENTS`. Every skill starts with Step 0: read `<cfp-context>` from the hook (plugin root, store path, whether the store is initialized). If the store is not initialized, every command except `/cfp:init` offers to run init first.

Interaction rules shared by all skills: one question at a time through AskUserQuestion; choices come from the effective profile where it defines them; every generated text is shown before it is saved; no em-dash or en-dash characters in generated prose.

## `/cfp:init`

**Arguments**: `[--store <path>]`

**Asks**: store path (default `~/Obsidian/<detected vault>/Talks` when a vault is found, else `~/cfp-store`), speaker name, company, voice profile (lists profiles from the prose plugin if present, allows none), review rounds (default 3).

**Does**: `config init` with the plugin's seed directory. Reports which profiles were seeded and where the store is.

**Output**: short summary with the store path and the next command to run.

## `/cfp:profile`

**Arguments**: `[new <conference name or CFP URL> | refresh <profile-id> [--event <event-id or URL>] | show <profile-id> | list] [--screenshots <path,...>]`

**new**: researches public CFP pages (WebSearch, WebFetch), reads screenshots (Read), fills a draft from `knowledge-base/guidance/profile-research.md`, presents it per section (session types, fields and limits, tracks and dates, rules and rubric) for approval. Each item shows `verified` with source or `unverified`. On approval, writes `profile.md` (and an event override when the input named a specific edition) with `approved: true`. Rejected sections are re-researched or entered manually.

**refresh**: for an existing profile, researches one event edition and writes or updates the event override with `approved: false`, then asks for approval per section. Asks before touching the family profile. With `--screenshots`, updates field limits and labels and marks them `screenshot`.

**show**: prints the effective profile for an event.

**list**: prints profiles with their events and days to CFP close.

## `/cfp:bio`

**Arguments**: `[new | list | edit <name> | delete <name> | resource add | resource list | resource delete <id>]`

**new**: asks emphasis, target length, and optional source material (existing bio, LinkedIn text, prior bios in the store); drafts a third-person bio in the configured voice; shows it with the character count; loops on edits; saves with `bio write`.

**edit**: loads, lets the user describe the change, redrafts, shows count, saves.

**resource add**: asks type, title, link, date; saves with `resource write`. Recommends adding a recording when none exists.

## `/cfp:draft`

**Arguments**: `[--profile <id>] [--event <id>] [--talk <id>] [--proposal <id>] [--from <path or URL>]`

**Flow** (each step saves, so the flow can resume from `--proposal`):

1. Profile and event: choose from `profile list`; if the event is missing, offer inline creation (FR-010a) via `/cfp:profile refresh` or manual entry (`event write` with `approved: true`). Warn when `cfp_close` is in the past.
2. Session type: choose from the effective event with duration and speaker limits shown; refuse types the solo speaker cannot satisfy unless co-speakers are confirmed and entered.
3. Input source: one-line idea, existing material (`--from`), existing talk, or existing proposal. For material, read it and pre-fill the story.
4. Story interview: fill every talk section (`talk complete` drives the questions), personas, projects, prior outings, resources. Save with `talk write`.
5. Angles: generate two or three title and abstract candidates following `knowledge-base/guidance/abstract-angles.md`; user picks or asks for another round. Save `angle`.
6. Field drafting: for every field in form order, draft per the field's guidance and limit; reviewer-only relevance fields follow `knowledge-base/guidance/benefits-field.md`; choice fields are asked, not generated; resources field offers `resource list` with recordings first; bio field offers `bio list` with counts and shortening. Save each with `proposal set-field`, `proposal set-meta`.
7. Committee review: `review packet`, spawn the `committee-reviewer` agent with the packet, `review record` the JSON. On `revise`, show scores and suggestions, apply accepted rewrites, repeat up to `review_rounds`.
8. Voice pass: `prose:humanizer` per prose field with the configured voice (skip with notice if unavailable; inline fallback if the skill returns usage text), recount with `count`.
9. Over-limit handling: offer to shorten any over-limit field, recount.
10. Pre-flight: `preflight`, add audience-level finding when the abstract and level disagree. Show findings with rule sources.
11. Ready: `status ready-check`; when possible, `status set --to ready`.
12. Paste view: `pasteview --format markdown`, printed in full.

**Output**: the paste view and the proposal path.

## `/cfp:check`

**Arguments**: `<proposal-id>` (or choose from `proposal list`)

**Does**: `preflight`, audience-level comparison, `count`; prints findings with severity and source, over-limit fields, and missing required fields. Offers to open the draft flow for fixes.

## `/cfp:status`

**Arguments**: `[list [--status <s>] | set <proposal-id> <status> [--date <d>] | reopen <proposal-id> [--event <id>]]`

**list**: table grouped by status with event, dates, and days to CFP close for drafts.

**set**: `status set`; reports side effects (calibration example added, outing recorded).

**reopen**: starts `/cfp:draft --talk <talk of proposal>` for a new event with the old proposal's fields shown for reference.

## Hook: `<cfp-context>`

The UserPromptSubmit hook fires only for prompts starting with `/cfp:` and injects:

```xml
<cfp-context>
<plugin-root>/path/to/installed/cfp</plugin-root>
<store>/path/to/store or empty</store>
<store-initialized>true|false</store-initialized>
<today>2026-10-09</today>
</cfp-context>
```

## Agent: `committee-reviewer`

Input: the review packet JSON (rubric, thresholds, rejection reasons, examples, drafted fields, level, track, session type). Behavior: reads only the packet, scores each criterion on the rubric scale with half steps, writes a two-sentence reviewer comment per criterion, lowers scores for the packet's rejection reasons, compares against examples for tone and structure, and returns exactly one JSON object matching the reviewer schema in `contracts/scripts.md`. It never rewrites fields itself; suggestions are instructions, not replacement text.
