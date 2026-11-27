# Contract: Store File Schemas

> **Historical record.** The KubeCon examples below show the profile of 2026-10-09 and predate the profile that ships today. See the note at the top of [spec.md](../spec.md).

Every file is UTF-8 markdown. Front matter is delimited by `---` lines at the top. The parser accepts: scalars (string, int, float, bool, ISO date), flat lists, lists of flat maps, and one nested map level. Multi-line strings use `|` block scalars. Unknown keys are preserved on rewrite. A file whose front matter does not parse is reported with path and line and skipped.

Sections in the body are `## <Heading>` lines; scripts locate sections by exact heading text. Text between headings belongs to the preceding heading.

## `<store>/config.md`

```markdown
---
speaker_name: Roland Huss
speaker_company: Red Hat
voice_profile: blog
review_rounds: 3
default_profile: kubecon
---
```

No body required.

## `<store>/profiles/<id>/profile.md`

```markdown
---
id: kubecon
name: KubeCon + CloudNativeCon
platform: sessionize
approved: true
seed_version: "2026-10-09"
sources:
  - https://events.linuxfoundation.org/kubecon-cloudnativecon-europe/program/cfp/
session_types:
  - id: session
    name: Session Presentation
    duration_min: 30
    min_speakers: 1
    max_speakers: 2
    notes: ""
  - id: panel
    name: Panel Discussion
    duration_min: 30
    min_speakers: 3
    max_speakers: 5
    notes: All panelists named at submission.
submission_limit: 3
selection_limit: 1 panel + 1 non-panel per event
fields:
  - id: title
    label: Session Title
    required: true
    kind: text
    limit: 75
    limit_status: unverified
    source: ""
    audience: public
    guidance: Title case. Follow the LF Inclusive Language Initiative.
  - id: abstract
    label: Session Description
    required: true
    kind: longtext
    limit: 1300
    limit_status: unverified
    source: ""
    audience: public
    guidance: Problem, contribution, relevance. Full sentences, third person.
  - id: benefits
    label: Benefits to the Ecosystem
    required: true
    kind: longtext
    limit: 1000
    limit_status: unverified
    source: ""
    audience: reviewer
    guidance: Who benefits, why now, what is new. Do not restate the abstract.
  - id: audience_level
    label: Level of Expertise for Intended Audience
    required: true
    kind: choice
    options:
      - Any
      - Beginner
      - Intermediate
      - Advanced
    audience: public
rubric:
  scale_max: 5
  pass_average: 4.0
  pass_min_criterion: 3.0
  criteria:
    - id: content
      name: Content
      description: Clear, coherent, engaging, high-impact takeaways.
    - id: originality
      name: Originality
      description: New angle, not generic, not a product pitch, not AI slop.
rules:
  - id: submission-limit
    kind: submission_limit
    severity: disqualify
    params:
      max: 3
    source: https://events.linuxfoundation.org/kubecon-cloudnativecon-europe/program/cfp/
    text: Max 3 proposals per speaker per event.
  - id: repeat-one-year
    kind: repeat_within_months
    severity: warn
    params:
      months: 12
    source: https://events.linuxfoundation.org/kubecon-cloudnativecon-europe/program/cfp/
    text: Talks presented at an LF event within the past year are not selected unless significantly different.
rejection_reasons:
  - Vendor or product pitch
  - Vague, generic, or AI-generated text
bio_limit: 500
bio_limit_status: unverified
---

## Drafting guidance

Free prose the draft skill reads before drafting.
```

Field `kind` values: `text`, `longtext`, `choice`, `multichoice`, `boolean`, `link`, `resources`. Rule `kind` values: `submission_limit`, `repeat_within_months`, `track_in_event`, `speaker_count`, `all_men_panel`, `multi_company_panel`, `vendor_pitch`, `custom`. Rules of kind `vendor_pitch` and `custom` are evaluated by the committee review, not by the script; the script lists them as "manual" in pre-flight output.

## `<store>/profiles/<id>/events/<event-id>.md`

```markdown
---
id: kubecon-eu-2027
profile: kubecon
name: KubeCon + CloudNativeCon Europe 2027
location: Barcelona
event_start: 2027-03-15
event_end: 2027-03-18
cfp_open: 2026-08-10
cfp_close: 2026-10-11
cfp_close_timezone: CEST
notification: 2026-12-07
approved: true
sources:
  - https://events.linuxfoundation.org/kubecon-cloudnativecon-europe/program/cfp/
tracks:
  - Agentic AI
  - AI Inference and Infrastructure
submission_limit: 3
session_type_overrides:
  - id: tutorial
    duration_min: 80
field_overrides: []
---
```

## `<store>/profiles/<id>/examples/<slug>.md`

```markdown
---
id: kubecon-eu-2027--my-talk
profile: kubecon
event: kubecon-eu-2027
year: 2027
origin: own-accepted
proposal: kubecon-eu-2027--my-talk
---

## Title

...

## Abstract

...

## Benefits

...
```

## `<store>/talks/<id>.md`

```markdown
---
id: agentic-platform-lessons
title: What Broke When We Put Agents on the Platform
status: active
created: 2026-10-09
updated: 2026-10-09
personas:
  - Platform engineers
  - SREs
projects:
  - Kubernetes
  - Argo CD
resources:
  - kubecon-eu-2025-recording
outings:
  - event: KubeCon EU 2025
    family: kubecon
    date: 2025-04-02
    link: https://youtu.be/...
    kind: presented
source_material:
  - https://ro14nd.de/blog/...
---

## Problem

## Contribution

## Takeaways

- ...

## What is new

## Story notes
```

## `<store>/proposals/<event-id>--<talk-id>.md`

```markdown
---
id: kubecon-eu-2027--agentic-platform-lessons
talk: agentic-platform-lessons
profile: kubecon
event: kubecon-eu-2027
session_type: session
track: Platform Engineering: DevEx & IDPs
audience_level: Intermediate
angle: problem-first
status: draft
created: 2026-10-09
updated: 2026-10-09
submitted_on:
decided_on:
presented_on:
ready_on:
bio_variation: short-cloud-native
resources:
  - kubecon-eu-2025-recording
co_speakers: []
co_speaker_genders: []
voice_pass: false
review_rounds:
  - round: 1
    date: 2026-10-09
    scores:
      content: 3.5
      originality: 4.0
    comments:
      content: Takeaways are implicit.
      originality: Fresh angle on agent failures.
    verdict: revise
    suggestions:
      - field: abstract
        text: State the three takeaways explicitly in the last paragraph.
review_stale: false
preflight:
  date: 2026-10-09
  ok: true
  findings: []
---

## Field: title

...

## Field: abstract

...

## Field: benefits

...

## Field: audience_level

Intermediate

## Bio

...
```

Field sections appear in the effective event's field order. Missing sections mean "not drafted yet". `review_stale` is set when a `ready` proposal is edited (or moved back to `draft`): the review history stays, but `ready` needs a new review round; `review record` clears it. The `preflight` map is emptied at the same time.

## `<store>/bios/<name>.md`

```markdown
---
name: short-cloud-native
emphasis: cloud-native
target_length: 450
updated: 2026-10-09
chars: 437
---

Roland Huss is ...
```

## `<store>/resources/<id>.md`

```markdown
---
id: kubecon-eu-2025-recording
type: recording
title: KubeCon EU 2025 session recording
link: https://youtu.be/...
date: 2025-04-02
notes: ""
---
```

## `~/.config/cc-cfp/config.json`

```json
{ "store": "/Users/me/Obsidian/vault/Talks" }
```

Environment variable `CFP_STORE` overrides the file when set.
