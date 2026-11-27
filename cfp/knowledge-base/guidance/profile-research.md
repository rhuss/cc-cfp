# Researching a conference profile

## Purpose

A profile turns public CFP pages, reviewer guideline pages, and submission form screenshots into structured data that the `cfp_store.py profile write` and `cfp_store.py event write` commands accept. The drafting skill reads that data to know which fields to draft, how long they may be, which options exist, and which rules disqualify a proposal. Research fills the schema; the user approves it; only then is it written.

The schema (the shipped `knowledge-base/profiles/kubecon/profile.md` and `events/kubecon-eu-2027.md` are the live reference) has these parts:

- Family profile: `id`, `name`, `platform`, `sources`, `session_types` (each with `id`, `name`, `duration_min`, `min_speakers`, `max_speakers`, `notes`), `submission_limit`, `selection_limit`, `fields`, `rubric`, `rules`, `rejection_reasons`, `bio_on_form`, `bio_limit`, `bio_limit_status`, and a `## Drafting guidance` body section.
- Each field: `id`, `label`, `required`, `kind` (one of `text`, `longtext`, `choice`, `multichoice`, `boolean`, `link`, `resources`), `limit`, `limit_status` (`unverified`, `page`, `screenshot`), `source`, `options` (for choice kinds), `audience` (`public` or `reviewer`), `guidance`.
- Rubric: `scale_max`, `pass_average`, `pass_min_criterion`, `criteria` (each with `id`, `name`, `description`).
- Each rule: `id`, `kind` (one of `submission_limit`, `repeat_within_months`, `track_in_event`, `speaker_count`, `all_men_panel`, `multi_company_panel`, `vendor_pitch`, `custom`), `severity`, `params`, `source`, `text`.
- Event override: `id`, `profile`, `name`, `location`, `event_start`, `event_end`, `cfp_open`, `cfp_close`, `cfp_close_timezone`, `notification`, `tracks`, `submission_limit`, `session_type_overrides`, `field_overrides`, `sources`.

Every value you put into the schema must be traceable to a page URL, a screenshot file, or a user statement. Record which one.

## From the CFP page

Fetch the official CFP page (and the pages it links, such as "sample submission", "rules", "co-located events"). Extract:

1. Session types: name, duration in minutes, minimum and maximum speaker count, and any notes (for example "all panelists named at submission"). One `session_types` entry each.
2. Submission limits per speaker (`submission_limit`) and any selection limit ("at most one panel plus one talk accepted").
3. Dates: CFP open, CFP close with its timezone as printed on the page, notification date, event start and end, and location. These go into the event override, not the family profile.
4. Tracks or topics for this edition. Tracks change every edition, so they belong in the event override as a list of exact strings.
5. Field descriptions: every form field the page describes in prose, its label, whether it is required, and any stated limit. If the page states no limit, keep the historic number from prior research and mark it `unverified`.
6. Hard rules: repeat policy (`repeat_within_months`), diversity composition rules (`all_men_panel`), panel company rules (`multi_company_panel`), vendor pitch policy (`vendor_pitch`), submission limits (`submission_limit`). Record the page's own wording in `text` and the URL in `source`. Set `severity` to `disqualify` when the page says the proposal is removed or not selected, otherwise `warn`.
7. Contact address for CFP questions and the submission platform (`platform`, for example `sessionize`, `pretalx`, `cfp.dev`).

## From reviewer guideline pages

Many conferences publish how reviewers score. Search for "reviewer guidelines", "scoring guidelines", or "program committee" pages. Extract:

1. Rubric criteria with the scale (`scale_max`) and a short description per criterion that captures what the top and bottom star levels mean. Put the per-level wording into the criterion `description` so the committee review can calibrate.
2. What reviewers are told to flag: audience level mismatch, wrong track, speaker on too many sessions, product pitch. Each becomes a `rejection_reasons` entry or a rule.
3. Pass behavior: how proposals move forward ("top 30 percent go to track chairs", "average above 4.0"). Use this to set `pass_average` and `pass_min_criterion`. If the page gives no number, set a defensible default and record it as an assumption in the `## Drafting guidance` section.

## From form screenshots

When the user supplies screenshots of the live form (file paths or pasted images), they are the most reliable source because the form itself is usually behind a login. Extract:

1. Exact field labels and their order on the form. Order the `fields` list the same way.
2. Required markers (asterisks, "required" text).
3. Character limits shown by counters ("0 / 1300") or help text ("max 75 characters").
4. Option lists for dropdowns and radio groups, verbatim, in the shown order.
5. Which fields are public versus reviewer-only, when the form or its help text says so.
6. Whether the form asks for a speaker bio with the submission, and its limit. When the screenshots cover the complete form and show no bio, set `bio_on_form: false` and leave `bio_limit` empty; the draft flow then attaches no bio and the paste view prints none. Without screenshots of the whole form, keep `bio_on_form: true`.

Each item taken from a screenshot gets `limit_status: screenshot` and `source: screenshot:<filename>`. Fields seen in a screenshot but absent from the CFP page are added, with the same source. Ask for the filename if an image was pasted without one and store it as `screenshot:pasted-<n>`.

## Verification status rules

- Every limit and every rule is one of: `page` with a URL in `source`, `screenshot` with `screenshot:<filename>` in `source`, or `unverified` with an empty source.
- Never upgrade a status without a source. A number the user remembers is `unverified`. A number from a blog post or a template from an earlier year is `unverified`, with the URL noted in the `## Drafting guidance` section for context.
- When a screenshot contradicts a page, the screenshot wins. Record the conflict in the profile's `## Notes` body section with both values and both sources, so the next refresh can re-check.
- When two pages disagree (for example the EU page and the NA page), prefer the page for the event being researched and record the other value in `## Notes`.

## When nothing public exists

If the form is login-walled and there is no CFP page, or the page is a single paragraph:

1. Build a minimal profile from what the user tells you: platform, session types, the fields they remember, the deadline.
2. Mark every limit `unverified` and every rule's source empty.
3. Suggest that the user open the form and take screenshots of each page, then re-run the profile command with those files. Say which items would become verified.
4. Still require approval before writing.

## How to present the draft for approval

Present one section at a time, and wait for an answer before moving on. The sections are:

1. Session types (with speaker counts and durations).
2. Fields and limits (label, kind, required, limit, options, audience).
3. Tracks and dates (for the event override).
4. Rules and rubric.
5. Rejection reasons and the speaker bio (on the form or not, and its limit).

Each item shows its value and its verification label in brackets, for example `abstract: longtext, required, limit 1300 [unverified]` or `cfp_close: 2026-10-11 CEST [page: https://...]`. After each section ask: approve, edit, or re-research? On edit, apply the change and show the section again. On re-research, go back to the sources for that section only.

Write only after approval. The family profile and each event override are approved separately: a user may approve the family profile and reject an event override, or approve an override for one edition while another stays unapproved. An override the user typed in manually counts as approved by the act of entering it. When refreshing an existing profile for a new edition, create or update the event override and ask before touching anything in the family profile.

## Field id conventions

Use snake_case ids so the drafting skill can recognize the same field across conferences:

- `title`: session title
- `abstract`: session description or abstract (public)
- `value_to_community` (or `benefits` on older forms): reviewer-only relevance field (value to the community, benefits to the ecosystem, notes to reviewers)
- `audience_level`: level of expertise for the intended audience
- `track`: track or topic selection
- `format`: session format or type selection
- `case_study`: boolean, is this an end-user case study
- `previously_presented`: boolean or text about prior outings of the talk
- `cncf_oss_projects`: CNCF projects featured plus all other open source projects discussed, with links (older forms split this into `cncf_projects` and `open_source_projects`)
- `resources`: additional resources such as prior recordings. Use kind `resources` when the form takes a list of links and `longtext` when it has one free-text box; the draft flow fills the field from the stored speaker resources either way

Fields that match none of these get a descriptive snake_case id of their own (for example `learning_outcomes`, `prerequisites`).

The speaker bio is not a field. Record it with the profile keys `bio_on_form`, `bio_limit`, and `bio_limit_status`, never as an entry in `fields`; the draft flow attaches a stored bio variation as its own part.

The draft flow treats exactly one field as the reviewer-only relevance field and writes it with the benefits guidance: `benefits` when the form has a field with that id, otherwise the first field in form order with `audience: reviewer` and `kind: longtext`, not counting `previously_presented` and `resources`. `profile show` reports its id as `relevance_field` (null when the form has none). Every other reviewer-only text field is drafted from its own `guidance`, so give those fields a `guidance` text that says what the form expects.
