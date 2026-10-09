# Contract: `cfp_store.py` CLI

Single entry point for every deterministic operation. Always invoked as:

```bash
python3 -I "$PLUGIN_ROOT/scripts/cfp_store.py" <subcommand> [options]
```

Conventions:

- Store resolution order: `--store <path>`, then env `CFP_STORE`, then `~/.config/cc-cfp/config.json`. Missing store is an error for every subcommand except `config init`.
- Output: a single JSON object on stdout. Success has `"ok": true`. Errors have `"ok": false, "error": "<message>"` on stdout and exit code 1. Usage errors exit 2.
- Dates are ISO `YYYY-MM-DD`. `--today` overrides the current date (for tests and repeat-rule checks).
- Write subcommands rewrite only the target file and preserve unknown front matter keys and body sections they do not own.
- No subcommand makes network calls.
- Every `list` subcommand (`profile list`, `event list`, `example list`, `talk list`, `bio list`, `resource list`, `proposal list`) also returns `problems: [{path, error}]` listing store files that were skipped because their front matter did not parse. The list itself contains only the readable files.

## config

| Subcommand | Input | Output |
|---|---|---|
| `config show` | | `{store, exists, config: {speaker_name, speaker_company, voice_profile, review_rounds, default_profile}}` |
| `config init --store <path> --speaker-name <s> [--speaker-company <s>] [--voice-profile <s>] [--review-rounds <n>] [--seed-dir <plugin knowledge-base/profiles>]` | Creates the folder tree, writes `config.md`, writes the user config file, copies every seed profile directory from `--seed-dir` that does not already exist in the store (sets `approved: true`, `seed_version`). | `{store, created: [paths], seeded_profiles: [ids]}` |
| `config set --key <k> --value <v>` | Updates one `config.md` key. | `{key, value}` |

## profile

| Subcommand | Input | Output |
|---|---|---|
| `profile list` | | `{profiles: [{id, name, approved, events: [{id, name, cfp_close, approved}]}]}` |
| `profile show --profile <id> [--event <id>]` | | Effective profile (merged with the event override when given): `{profile, event, session_types, fields, rubric, rules, submission_limit, bio_limit, bio_limit_status, tracks, approved}` |
| `profile validate --profile <id> [--event <id>]` | Schema checks from data-model.md. | `{valid, problems: [text]}` |
| `profile write --profile <id> --from-json <file>` | Writes `profile.md` from a JSON document (used after research). Body sections passed as `body: {"Drafting guidance": "..."}`. | `{path}` |
| `profile approve --profile <id> [--event <id>] [--revoke]` | Sets `approved`. | `{path, approved}` |
| `event write --profile <id> --event <id> --from-json <file>` | Writes an override file. `approved` taken from the JSON (default false). | `{path}` |
| `event list --profile <id>` | | `{events: [...]}` with days until `cfp_close` relative to today |
| `example add --profile <id> --from-json <file>` | Adds a calibration example (`title`, `abstract`, `benefits`, `event`, `year`, `origin`, `proposal`). | `{path}` |
| `example list --profile <id> [--limit <n>]` | Newest first. | `{examples: [{id, event, year, origin, title, abstract, benefits}]}` |

## talk

| Subcommand | Input | Output |
|---|---|---|
| `talk list [--status active]` | | `{talks: [{id, title, status, updated, proposals: [ids], last_presented}]}` |
| `talk show --talk <id>` | | Front matter plus body sections as `sections: {Problem, Contribution, Takeaways, ...}` |
| `talk write --talk <id> --from-json <file>` | Creates or updates; `id` generated from `title` when absent; `updated` set. Sections passed as `sections` map. | `{path, id, created: bool}` |
| `talk complete --talk <id>` | Reports which story sections are empty and which front matter lists are empty (`personas`). | `{complete: bool, missing: [section], missing_meta: [key]}` |

## bio and resource

| Subcommand | Input | Output |
|---|---|---|
| `bio list` | | `{bios: [{name, emphasis, target_length, chars, updated}]}` |
| `bio show --name <n>` | | `{name, emphasis, target_length, chars, text}` |
| `bio write --name <n> --emphasis <s> --target-length <n> --text-file <file>` | Creates or updates; recounts `chars`. | `{path, chars}` |
| `bio delete --name <n>` | | `{deleted: path}` |
| `resource list [--type <t>]` | | `{resources: [...]}` |
| `resource write --from-json <file>` | | `{path, id}` |
| `resource delete --id <id>` | | `{deleted}` |

## proposal

| Subcommand | Input | Output |
|---|---|---|
| `proposal list [--status <s>] [--event <id>] [--talk <id>]` | Grouped by status when no filter. | `{proposals: [{id, talk, title, profile, event, status, updated, submitted_on, decided_on}]}` |
| `proposal show --proposal <id>` | | Front matter plus `fields: {field-id: text}` and `bio` |
| `proposal create --talk <id> --profile <id> --event <id> --session-type <id> [--angle <s>]` | Refuses if a proposal for the same talk and event exists, if the profile or event is not approved, or if the session type is unknown. | `{path, id}` |
| `proposal set-field --proposal <id> --field <field-id> --text-file <file>` | Writes one `## Field:` section. Unknown field id is an error. `track` and `audience_level` are mirrored into the front matter. | `{field, chars, limit, limit_status, status}` where `status` is `ok`, `over`, `unverified`, `no-limit`; plus `reset_to_draft: true` when a `ready` proposal was demoted |
| `proposal set-meta --proposal <id> [--from-json <file>] [--track <s>] [--audience-level <s>] [--bio <name>] [--resources <id,id>] [--co-speakers <json>] [--co-speaker-genders <json>] [--angle <s>] [--session-type <id>]` | Updates front matter; `--bio` also copies the bio text into `## Bio` (snapshot). `--from-json` carries the same keys (snake_case) so free text never travels as a shell argument; flags win over the file. | `{updated: [keys]}` plus `reset_to_draft` as above |
| `proposal set-bio-text --proposal <id> --text-file <file>` | Replaces the bio snapshot only (shortened or voiced). | `{chars, limit, status}` plus `reset_to_draft` as above |
| `proposal mark-voice-pass --proposal <id>` | Sets `voice_pass: true`. | `{voice_pass: true}` |
| `count --proposal <id>` | Counts every drafted field and the bio against effective limits. | `{fields: [{id, label, required, chars, limit, limit_status, status, drafted}], bio: {...}, over: [ids], missing_required: [ids]}` |
| `pasteview --proposal <id> [--format markdown\|json]` | Renders fields in form order with counts; flags over-limit and unverified limits. Also stores nothing. | markdown text (when `--format markdown`, stdout is the markdown, not JSON) |

## review

| Subcommand | Input | Output |
|---|---|---|
| `review packet --proposal <id> [--examples <n>]` | Builds the reviewer input: rubric, pass thresholds, rejection reasons, up to `n` calibration examples (default 3), drafted fields, audience level, track, session type. | `{packet: {...}}` |
| `review record --proposal <id> --from-json <file>` | Validates the reviewer JSON (`scores` for every criterion, `comments`, `suggestions`), appends a round, computes `verdict` from thresholds (reviewer verdict is advisory). | `{round, verdict, average, below_min: [criterion], suggestions}` |
| `review history --proposal <id>` | | `{rounds: [...]}` |

Reviewer JSON schema (produced by the `committee-reviewer` agent):

```json
{
  "scores": {"content": 3.5, "originality": 4.0, "relevance": 4.5, "speaker": 4.0, "not_product_pitch": 5.0},
  "comments": {"content": "...", "originality": "...", "relevance": "...", "speaker": "...", "not_product_pitch": "..."},
  "verdict": "revise",
  "suggestions": [{"field": "abstract", "text": "..."}]
}
```

## preflight

| Subcommand | Input | Output |
|---|---|---|
| `preflight --proposal <id> [--today <date>]` | Evaluates every rule of the effective profile (see rule kinds below), stores the result in the proposal's `preflight` map (whose `ok` key is the rule verdict). | `{passed, findings: [{rule, kind, severity, text, source}], manual: [{rule, kind, text, source}], problems: [{path, error}]}` where `passed` is true when no `disqualify` finding exists (the top-level `ok` keeps its usual meaning: the call succeeded) and `problems` lists proposal files that could not be parsed and therefore were not counted |
| `preflight add-finding --proposal <id> [--from-json <file>] [--rule <id>] [--severity disqualify\|warn] [--text <s>] [--source <s>]` | Appends a manual finding (for example the audience level comparison) to the stored `preflight` map and recomputes its `ok`. `--from-json` carries `rule`, `severity`, `text`, `source` so the reason text never travels as a shell argument; flags win over the file. | `{passed, findings}` |

Rule evaluation:

| kind | Evaluation |
|---|---|
| submission_limit | Count proposals (once per id) for the same event with status in {submitted, accepted, rejected, presented}, excluding this proposal; finding when count is at or above the limit. The limit is the event override's `submission_limit` when set, else `params.max`, else the profile's `submission_limit`. Unreadable proposal files produce a `warn` finding naming them. |
| repeat_within_months | Talk outings of kind `presented` with `family` equal to the proposal's profile and `date` within `params.months` before today; severity downgraded to `warn` when the proposal's note field (`params.note_field`, default `previously_presented`) is non-empty. |
| track_in_event | `track` not in the event's `tracks` (case-insensitive). Disqualify. |
| speaker_count | 1 + len(co_speakers) outside the session type's min and max. Disqualify. |
| all_men_panel | Applies when total speakers is 3 or more and every `co_speaker_genders` entry plus the speaker's configured gender (optional config key `speaker_gender`) equals `man` (`male` and `m` count as `man`); `unknown`, `n/a`, and empty count as unknown and emit a `warn` asking to confirm. |
| multi_company_panel | Applies to session types with min_speakers of 3 or more: all co-speaker company parts equal to the speaker's company. Disqualify. |
| vendor_pitch, custom | Not evaluated; listed under `manual` for the committee review. |

Audience level mismatch (FR-029) is not a script rule. The check skill asks the model to compare the abstract against the chosen level and adds a `warn` finding with `rule: audience-level` through `preflight add-finding --proposal <id> --rule audience-level --severity warn --text "<reason>"`.

## status

| Subcommand | Input | Output |
|---|---|---|
| `status set --proposal <id> --to <status> [--date <date>] [--force]` | Validates the transition (state machine in data-model.md, plus `ready -> draft` and `accepted -> withdrawn`), sets the date field, performs side effects: `accepted` adds a calibration example; `presented` appends a `presented` outing to the talk; `draft` clears `ready_on` and marks the checks stale; `ready` requires the last review verdict to be `pass`, no stale review, and `preflight.ok` to be true unless `--force`. | `{from, to, date, side_effects: [text]}` |
| `status ready-check --proposal <id>` | Reports whether automatic ready is possible. | `{can_ready, reasons: [text]}` |

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Domain error (invalid transition, unknown id, unapproved profile, parse failure) |
| 2 | Usage error (bad arguments) |
