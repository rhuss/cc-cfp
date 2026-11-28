# Data Model: CFP and Bio Plugin

**Date**: 2026-10-09 | **Feature**: 001-cfp-plugin

All entities are markdown files with YAML front matter (subset defined in research.md R3). Body text below the front matter holds long prose (abstracts, bios, stories) under fixed `##` headings so scripts can locate sections. Exact file schemas are in [contracts/store-files.md](contracts/store-files.md).

## Entity overview

```text
UserConfig (1) ──> Store (1)
Store ──> StoreConfig (1)
Store ──> Profile (many) ──> EventOverride (many)
                        └──> CalibrationExample (many)
Store ──> Talk (many) ──> Proposal (many)
Proposal ──> EventOverride (1), BioVariation (1, by name + snapshot), SpeakerResource (0..n)
Proposal ──> ReviewRound (0..n, embedded)
Store ──> BioVariation (many)
Store ──> SpeakerResource (many)
Talk ──> SpeakerResource (0..n, by slug)
Talk ──> Outing (0..n, embedded)
```

## UserConfig

Location: `~/.config/cc-cfp/config.json` (override with env `CFP_STORE` for tests and scripts).

> **Note**: Superseded by feature 002: the default store is `<data folder>/store` and the config folder follows XDG; see specs/002-xdg-config-store/spec.md.

| Field | Type | Rules |
|---|---|---|
| store | string (absolute path) | Required. Created on init if missing. |

## StoreConfig

Location: `<store>/config.md`.

| Field | Type | Rules |
|---|---|---|
| speaker_name | string | Required. Used in third-person bios and drafts. |
| speaker_company | string | Optional. |
| voice_profile | string | Optional. Name passed to the prose plugin. Empty means "no voice, humanize only". |
| review_rounds | int | Default 3. Max committee review rounds before the loop stops. |
| default_profile | string | Optional. Profile id offered first in drafting. |

## Profile

Location: `<store>/profiles/<id>/profile.md`.

| Field | Type | Rules |
|---|---|---|
| id | slug | Equals directory name. |
| name | string | Display name, e.g. "KubeCon + CloudNativeCon". |
| platform | string | e.g. "sessionize". Informational. |
| approved | bool | Drafting refuses profiles with `approved: false`. |
| seed_version | string | Set when copied from the knowledge base; empty for researched profiles. |
| sources | list of string | URLs used during research. |
| session_types | list of map | Each: `id`, `name`, `duration_min` (int or null), `min_speakers`, `max_speakers`, `notes`. |
| submission_limit | int | Max proposals per speaker per event. Null means no limit. |
| selection_limit | string | Free text, e.g. "1 panel + 1 non-panel". |
| fields | list of map | Ordered form fields. Each: `id`, `label`, `required` (bool), `kind` (text, longtext, choice, multichoice, boolean, link, resources), `limit` (int or null), `limit_status` (unverified, page, screenshot), `source` (URL or `screenshot:<file>` or empty), `options` (list, for choice kinds), `audience` (public, reviewer), `guidance` (string). |
| rubric | map | `scale_max` (int), `pass_average` (float), `pass_min_criterion` (float), `criteria`: list of map `id`, `name`, `description`. |
| rules | list of map | Hard rules. Each: `id`, `kind` (submission_limit, repeat_within_months, track_in_event, speaker_count, all_men_panel, multi_company_panel, vendor_pitch, custom), `severity` (disqualify, warn), `params` (map), `source` (string), `text` (string). |
| rejection_reasons | list of string | Reference for the committee review. |
| bio_limit | int or null | Character limit for the speaker bio. |
| bio_limit_status | string | unverified, page, screenshot. |

Body sections: `## Drafting guidance` (free prose the draft skill reads), `## Notes`.

**Validation**: `fields[].id` unique; every `rules[].kind` in the enum; `rubric.criteria` non-empty when the profile is approved; `session_types[].id` unique.

## EventOverride

Location: `<store>/profiles/<profile-id>/events/<event-id>.md`.

| Field | Type | Rules |
|---|---|---|
| id | slug | e.g. `kubecon-eu-2027`. |
| profile | slug | Parent profile id. |
| name | string | e.g. "KubeCon + CloudNativeCon Europe 2027". |
| location | string | Optional. |
| event_start, event_end | date | Optional. |
| cfp_open, cfp_close | date | Optional. `cfp_close` drives the deadline warning. |
| cfp_close_timezone | string | Optional, informational. |
| notification | date | Optional. |
| approved | bool | Research-created overrides start `false`; manual entries start `true`. |
| sources | list of string | |
| tracks | list of string | Track list for this edition. Required for track checks. |
| submission_limit | int or null | Overrides the profile value when set. |
| session_type_overrides | list of map | Same shape as `session_types`; merged by `id`, replacing matching entries, adding new ones. `remove: true` drops a type for this edition. |
| field_overrides | list of map | Same shape as `fields`; merged by `id` (replace matching keys only). |

**Merge rule** (profile.py): effective event = profile with `submission_limit`, `session_types`, and `fields` patched by the override. Scripts always operate on the effective event.

## CalibrationExample

Location: `<store>/profiles/<profile-id>/examples/<slug>.md`.

| Field | Type | Rules |
|---|---|---|
| id | slug | |
| profile | slug | |
| event | slug or string | Event id when from own proposal, free text for external samples. |
| year | int | |
| origin | string | `own-accepted`, `official-sample`, `manual`. |
| proposal | slug or empty | Set when origin is `own-accepted`. |

Body sections: `## Title`, `## Abstract`, `## Benefits` (optional), `## Why it worked` (optional notes).

## Talk

Location: `<store>/talks/<id>.md`.

| Field | Type | Rules |
|---|---|---|
| id | slug | From working title. |
| title | string | Working title. |
| status | string | `active`, `retired`. |
| created, updated | date | |
| personas | list of string | Target audience personas. |
| projects | list of string | Open source projects involved (names or URLs). |
| resources | list of slug | SpeakerResource ids linked to this talk. |
| outings | list of map | Each: `event` (string or event id), `family` (profile id or empty), `date` (date), `link` (string), `kind` (presented, submitted). Only `presented` outings feed the repeat rule. |
| source_material | list of string | Links or paths the story was derived from. |

Body sections (all required for a complete story; the draft skill fills them through the interview): `## Problem`, `## Contribution`, `## Takeaways` (bullet list), `## What is new`, `## Story notes` (free text, hard parts, lessons learned).

## Proposal

Location: `<store>/proposals/<event-id>--<talk-id>.md`.

| Field | Type | Rules |
|---|---|---|
| id | slug | `<event-id>--<talk-id>`. Unique per talk and event. |
| talk | slug | |
| profile | slug | |
| event | slug | |
| session_type | string | Session type id from the effective event. |
| track | string | Must be in `event.tracks` (checked by pre-flight). |
| audience_level | string | One of the field's options. |
| angle | string | Short label of the chosen angle. |
| status | string | See state machine. |
| created, updated | date | |
| submitted_on, decided_on, presented_on | date | Set by status transitions. |
| bio_variation | string | Name of the chosen BioVariation. |
| resources | list of slug | Chosen SpeakerResource ids. |
| co_speakers | list of string | Free text "Name, Company". Used for speaker count and composition rules. |
| co_speaker_genders | list of string | Optional free text per co-speaker; only used for the all-men rule when provided. |
| review_rounds | list of map | Each: `round` (int), `date`, `scores` (map criterion id to float), `comments` (map criterion id to string), `verdict` (pass, revise), `suggestions` (list of map `field`, `text`). |
| preflight | map | Last run: `date`, `findings` (list of map `rule`, `severity`, `text`), `ok` (bool). |
| voice_pass | bool | True once the voice pass ran. |
| ready_on | date | Set when status becomes ready. |

Body: one `## Field: <field-id>` section per form field holding the drafted text, plus `## Bio` holding the bio snapshot. Field sections appear in the profile's field order. Choice-kind fields store the chosen option as a single line.

### Proposal status state machine

```text
draft ──(review pass + preflight ok, or manual)──> ready
draft, ready ──(status submitted)──> submitted
submitted ──(accepted)──> accepted ──(presented)──> presented
submitted ──(rejected)──> rejected
draft, ready, submitted ──(withdrawn)──> withdrawn
rejected, withdrawn ──(reopen)──> new Proposal (different event or re-created after withdraw); source proposal keeps its status
```

Transitions set the matching date (`submitted_on`, `decided_on`, `presented_on`, `ready_on`). `accepted` appends a CalibrationExample (FR-033). `presented` appends a `presented` outing to the talk (FR-034). Any other transition is rejected by `lifecycle.py` with an error naming the allowed targets.

### Submission limit counting

Statuses `submitted`, `accepted`, `rejected`, `presented` count toward `submission_limit` for the same event. `draft`, `ready`, `withdrawn` do not.

## BioVariation

Location: `<store>/bios/<name>.md`.

| Field | Type | Rules |
|---|---|---|
| name | slug | File name. |
| emphasis | string | e.g. "cloud-native", "ai", "general". |
| target_length | int | Characters the author aims for. |
| updated | date | |
| chars | int | Maintained by the script on every save (count of body text). |

Body: the bio text (third person), no headings.

## SpeakerResource

Location: `<store>/resources/<id>.md`.

| Field | Type | Rules |
|---|---|---|
| id | slug | |
| type | string | recording, repository, blog, session, publication, other. |
| title | string | |
| link | string | URL. |
| date | date | Optional. |
| notes | string | Optional. |

Body: optional description.

## Derived values (never stored, always computed)

- Effective event (profile merged with override).
- Character count per proposal field and limit status (`ok`, `over`, `unverified`, `no-limit`).
- Submission count per event.
- Repeat-rule window: talk outings of kind `presented` whose `family` equals the proposal's profile and whose `date` is within 365 days before today.
- Paste view (ordered fields with counts).
