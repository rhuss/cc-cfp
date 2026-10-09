---
id: kubecon
name: KubeCon + CloudNativeCon
platform: sessionize
approved: true
seed_version: "2026-10-09"
sources:
  - https://events.linuxfoundation.org/kubecon-cloudnativecon-europe/program/cfp/
  - https://events.linuxfoundation.org/kubecon-cloudnativecon-north-america/program/cfp/
  - https://events.linuxfoundation.org/kubecon-cloudnativecon-europe/program/submission-reviewer-guidelines/
  - https://events.linuxfoundation.org/wp-content/uploads/2023/01/CNCF-hosted-Co-located-Events-Europe-2023-CFP-1.pdf
  - https://gist.github.com/reylejano/b78b054e3d6943c330d6852501d4d7df
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
    notes: All panelists named at submission. Panelists must represent more than one company.
  - id: lightning
    name: Lightning Talk
    duration_min: 5
    min_speakers: 1
    max_speakers: 1
    notes: ""
  - id: tutorial
    name: Tutorial
    duration_min: 75
    min_speakers: 1
    max_speakers: 5
    notes: Hands-on. 80 minutes at EU 2027, 75 minutes elsewhere.
  - id: poster
    name: Poster Session
    duration_min:
    min_speakers: 1
    max_speakers: 2
    notes: Digital poster at a monitor in the Solutions Showcase. EU and NA only. Counts toward the proposal limit.
submission_limit: 3
selection_limit: At most 1 panel and 1 non-panel session per speaker per event, excluding project benefits.
fields:
  - id: title
    label: Session Title
    required: true
    kind: text
    limit: 75
    limit_status: unverified
    source: ""
    audience: public
    guidance: Title case. Must follow the LF Inclusive Language Initiative. Attendees pick talks by title, so name the concrete technology or outcome. Historic limit 75 characters, not confirmed on the live form.
  - id: abstract
    label: Session Description
    required: true
    kind: longtext
    limit: 1300
    limit_status: unverified
    source: ""
    audience: public
    guidance: Emphasize the problem, your contribution, and its relevance. The first two sentences carry the value proposition. Full sentences, third person (use the speaker name instead of I), no bullet lists. State takeaways explicitly. Published verbatim on the schedule. Historic limit 1300 characters.
  - id: benefits
    label: Benefits to the Ecosystem
    required: true
    kind: longtext
    limit: 1000
    limit_status: unverified
    source: ""
    audience: reviewer
    guidance: Reviewer-only. The second determining factor after the abstract. Say who benefits (by persona), why now, what is new compared with prior talks, your credentials and evidence, and what data or case study you will show. Do not restate the abstract. Historic limit 1000 characters.
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
    guidance: Reviewers check that the level matches the content and may correct it. Pick the level the abstract actually serves.
  - id: track
    label: Topic
    required: true
    kind: choice
    options: []
    audience: public
    guidance: Single select from the event's track list (filled from the event override). Wrong track is a top rejection reason. The list is a rough guideline, pick the closest fit.
  - id: format
    label: Session Format
    required: true
    kind: choice
    options:
      - Session Presentation
      - Panel Discussion
      - Lightning Talk
      - Tutorial
      - Poster Session
    audience: public
    guidance: Matches the chosen session type.
  - id: case_study
    label: Is this a case study?
    required: true
    kind: boolean
    audience: reviewer
    guidance: Yes when the talk reports on an organization's real-world implementation of a practice, product, system, or service and how well it worked. End-user case studies are favored for program balance.
  - id: previously_presented
    label: Has this presentation been given before?
    required: true
    kind: longtext
    limit:
    limit_status: unverified
    source: ""
    audience: reviewer
    guidance: If the talk was given at a CNCF or LF event within the past year, explain the significant differences (new data, new scope, new results). Otherwise state that it has not been presented before. Mention a link to slides or video of the previous outing when one exists.
  - id: cncf_projects
    label: CNCF-hosted software
    required: true
    kind: text
    limit:
    limit_status: unverified
    source: ""
    audience: reviewer
    guidance: Comma-separated CNCF project names (graduated, incubating, or sandbox) as listed on the form that the presentation focuses on. Use the exact project names.
  - id: open_source_projects
    label: Open source projects
    required: true
    kind: text
    limit:
    limit_status: unverified
    source: ""
    audience: reviewer
    guidance: All open source projects discussed, with links, including non-CNCF projects.
  - id: resources
    label: Additional Resources
    required: false
    kind: resources
    limit:
    limit_status: unverified
    source: ""
    audience: reviewer
    guidance: Optional on the form but decisive for the Speaker criterion. Link a video or audio recording of a previous talk first. Up to three resources, each with a type (Presentation Recording, Published Book, Personal Website, Open Source Project, Other) and a link. Without a recording, a short self-recorded YouTube video is suggested by the LF page.
rubric:
  scale_max: 5
  pass_average: 4.0
  pass_min_criterion: 3.0
  criteria:
    - id: content
      name: Content
      description: 1 star is unclear, incoherent, incomplete, or AI-generated. 3 stars is clear and structured but predictable or lacking depth. 4 stars is well written, coherent, a strong fit for the format and level. 5 stars is highly engaging, polished, with high-impact audience takeaways.
    - id: originality
      name: Originality
      description: 1 star is generic, copied, a product pitch, or AI slop. 3 stars is interesting ideas but presented before or lacking clear updates. 4 stars is a clear new angle or innovative approach. 5 stars is bold, highly creative, novel insights for KubeCon.
    - id: relevance
      name: Relevance
      description: 1 star is not relevant to CNCF or KubeCon with little audience value. 3 stars is relevant but narrow or niche. 4 stars is strongly aligned with conference goals and broad audience value. 5 stars is timely, significant cloud native challenges with wide community impact. The benefits field feeds this criterion.
    - id: speaker
      name: Speaker
      description: 1 star is examples of unengaging presentations or weak slides. 2 stars is no examples of presentation experience and unclear depth with the topic. 3 stars is personal experience with the topic and engaging content creation such as blogs or docs. 4 stars is topic expertise and clear examples of presented content. 5 stars is a recognized leader with recorded examples of engaging talks.
    - id: not_product_pitch
      name: Not a Product Pitch
      description: 1 star is a clear focus on proprietary software without wider ecosystem value. 3 stars is reviewer uncertain, with a comment. 5 stars is non-proprietary software with no signs of vendor pitching.
rules:
  - id: submission-limit
    kind: submission_limit
    severity: disqualify
    params:
      max: 3
    source: https://events.linuxfoundation.org/kubecon-cloudnativecon-europe/program/cfp/
    text: A speaker may be listed on at most 3 proposals per event in any format. Exceeding the limit may remove all proposals from review, including those with co-speakers.
  - id: repeat-one-year
    kind: repeat_within_months
    severity: disqualify
    params:
      months: 12
      note_field: previously_presented
    source: https://events.linuxfoundation.org/kubecon-cloudnativecon-europe/program/cfp/
    text: Talks presented at a CNCF or LF event within the past year are not selected unless the submission explains significant differences. Downgraded to a warning when the previously-presented field explains the differences.
  - id: track-in-event
    kind: track_in_event
    severity: disqualify
    params: {}
    source: https://events.linuxfoundation.org/kubecon-cloudnativecon-europe/program/submission-reviewer-guidelines/
    text: The chosen track must be one of the event's tracks. Reviewers flag wrong-track submissions and co-chairs name it a top rejection reason.
  - id: speaker-count
    kind: speaker_count
    severity: disqualify
    params: {}
    source: https://events.linuxfoundation.org/kubecon-cloudnativecon-europe/program/cfp/
    text: The number of speakers must fit the session format (session 1 to 2, panel 3 to 5, lightning 1, tutorial 1 to 5, poster 1 to 2).
  - id: all-men-panel
    kind: all_men_panel
    severity: disqualify
    params:
      min_speakers: 3
    source: https://events.linuxfoundation.org/kubecon-cloudnativecon-europe/program/cfp/
    text: CNCF does not accept any session with three or more speakers who all identify as men. Applies to panels and tutorials.
  - id: multi-company-panel
    kind: multi_company_panel
    severity: disqualify
    params: {}
    source: https://events.linuxfoundation.org/kubecon-cloudnativecon-europe/program/cfp/
    text: Panelists must represent more than one company.
  - id: vendor-pitch
    kind: vendor_pitch
    severity: disqualify
    params: {}
    source: https://events.linuxfoundation.org/kubecon-cloudnativecon-europe/program/cfp/
    text: No sales or marketing pitches. Unlicensed or potentially closed-source technologies are almost always rejected. Evaluated by the committee review.
rejection_reasons:
  - Vendor or product pitch, or closed-source focus (1 star Originality and Not a Product Pitch; reviewers can smell it from a mile away)
  - Vague, generic, bullet-list-only, or AI-generated text (1 star Content and Originality; repeat offenders can be banned)
  - Duplicate of a talk given at any LF event in the past year, or one of many similar submissions on a hot topic (Originality capped at 3 stars)
  - Missing or unclear takeaways and audience value; co-chairs want the hard parts and lessons learned
  - Wrong track or mislabeled audience level
  - No evidence of speaking ability (Speaker criterion gives 2 stars without examples of presentation experience)
  - Rule violations that remove the proposal from review (more than 3 submissions, 3 or more speakers all identifying as men, panelists from a single company, panelists not named at submission)
  - Program balance rather than quality (same speaker or company already selected, too many talks in one niche, diversity targets)
bio_limit: 500
bio_limit_status: unverified
---

## Drafting guidance

Reviewers in a track handle 100 to 200 proposals each and score in Sessionize star-rating mode. The first sentence of the abstract is where the proposal makes its impression, and the first two sentences must carry the value proposition: what problem the audience has and what the session gives them. Acceptance has fallen to around 8 to 11 percent, so a generic abstract on a hot topic loses to a specific one.

Write the abstract in third person with the speaker's name instead of "I". Use full sentences and short paragraphs, never a bullet list. Emphasize the problem, the contribution, and its relevance, with technical details that do not lose the big picture. State the takeaways explicitly ("Attendees will leave with ..."). Co-chairs look for the full story: the hard parts, what was learned, what is still unknown. An honest ending beats a perfect one.

The benefits field is reviewer-only and is the second determining factor after the abstract. It is not a copy of the abstract. Say who benefits by persona and what each gains, why the topic matters now, what is new versus prior talks, which credentials and evidence back the speaker, and what data or case study the session shows.

Pick the track carefully; many strong proposals are submitted under the wrong track. Choose the audience level the abstract really serves, because reviewers correct mismatches and penalize them. Link a recording of a previous talk in the resources field, since the Speaker criterion only reaches 5 stars with recorded examples of engaging talks. Focus on open source project work and keep vendor or product language out of every field. Reviewers prefer a typo over AI-flattened text, so keep the speaker's own phrasing.

The character limits in this profile (title 75, abstract 1300, benefits 1000, bio 500) are historic values from older forms and templates. The live Sessionize form sits behind a login, so treat them as soft targets until confirmed with screenshots.

## Notes

Seeded from brainstorm/research/kubecon-cfp-research.md on 2026-10-09. Co-located Day 0 events, the project benefits CFP (Maintainer Track, Project Lightning Talks, ContribFest), and the Maintainer Summit use separate Sessionize CFPs with different formats and limits; they need their own profiles or event overrides.
