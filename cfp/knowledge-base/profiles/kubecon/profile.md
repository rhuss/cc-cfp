---
id: kubecon
name: KubeCon + CloudNativeCon
platform: sessionize
approved: true
seed_version: "2026-10-11"
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
    guidance: Title case. Must follow the LF Inclusive Language Initiative. Attendees pick talks by title, so name the concrete technology or outcome. Historic limit 75 characters, not confirmed on the live form. No speaker or company names in the title.
  - id: abstract
    label: Description
    required: true
    kind: longtext
    limit: 1000
    limit_status: screenshot
    source: screenshot:sessionize-kubecon-eu-2027-2026-10-11
    audience: public
    guidance: Describe what attendees will learn, who the talk is for, and the key takeaways. Problem in the first two sentences, then the contribution, then explicit takeaways. Full sentences, session-centric (no speaker or company names), no bullet lists. Hard limit 1000 characters, confirmed on the live form.
  - id: value_to_community
    label: Value to the community
    required: true
    kind: longtext
    limit:
    limit_status: screenshot
    source: screenshot:sessionize-kubecon-eu-2027-2026-10-11
    audience: reviewer
    guidance: Why is this talk important, relevant, and timely to the cloud native ecosystem? Name who benefits and what changed now that makes it timely; do not restate the abstract. No character limit shown on the form.
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
    label: Case study?
    required: true
    kind: boolean
    audience: reviewer
    guidance: Yes when the talk reports on an organization's real-world implementation of a practice, product, system, or service and how well it worked. End-user case studies are favored for program balance.
  - id: previously_presented
    label: Talk presented before?
    required: true
    kind: longtext
    limit:
    limit_status: unverified
    source: ""
    audience: reviewer
    guidance: If the talk was given at a CNCF or LF event within the past year, explain the significant differences (new data, new scope, new results). Otherwise state that it has not been presented before. Mention a link to slides or video of the previous outing when one exists.
  - id: cncf_oss_projects
    label: Relevant CNCF/Open Source Projects
    required: true
    kind: text
    limit:
    limit_status: screenshot
    source: screenshot:sessionize-kubecon-eu-2027-2026-10-11
    audience: reviewer
    guidance: List the CNCF project(s) featured in your presentation, plus any other open source projects discussed. Use exact project names, with links where useful.
  - id: resources
    label: Additional resources
    required: false
    kind: longtext
    limit:
    limit_status: screenshot
    source: screenshot:sessionize-kubecon-eu-2027-2026-10-11
    audience: reviewer
    guidance: "Free text on the live form. Put speaker evidence here: recordings of previous talks for every speaker (the Speaker criterion reaches 5 only with recordings), project links, books, websites. Keep credentials out of the public abstract."
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
bio_limit_status: screenshot
---

## Drafting guidance

Reviewers in a track handle 100 to 200 proposals each and score in Sessionize star-rating mode. The first sentence of the abstract is where the proposal makes its impression, and the first two sentences must carry the value proposition: what problem the audience has and what the session gives them. Acceptance has fallen to around 8 to 11 percent, so a generic abstract on a hot topic loses to a specific one.

Write the abstract session-centric, not person-centric: refer to the talk as "this session" and do not name the speakers or their employers (accepted KubeCon abstracts almost never do; names and companies belong in the speaker profile and the bio). A role statement such as "both speakers are active in the X community" is acceptable. "We" appears in accepted abstracts but "I" does not. Use full sentences and short paragraphs, never a bullet list. When the session includes a live demo, say so and name what the demo shows; accepted abstracts state this explicitly. Emphasize the problem, the contribution, and its relevance, with technical details that do not lose the big picture. State the takeaways explicitly ("Attendees will leave with ..."). Co-chairs look for the full story: the hard parts, what was learned, what is still unknown. An honest ending beats a perfect one.

The "Value to the community" field (formerly "Benefits to the Ecosystem") is reviewer-only and is the second determining factor after the abstract. It is not a copy of the abstract. Say who benefits by persona and what each gains, why the topic matters now, what is new versus prior talks, which credentials and evidence back the speaker, and what data or case study the session shows.

Pick the track carefully; many strong proposals are submitted under the wrong track. Choose the audience level the abstract really serves, because reviewers correct mismatches and penalize them. Link a recording of a previous talk in the resources field, since the Speaker criterion only reaches 5 stars with recorded examples of engaging talks. Focus on open source project work and keep vendor or product language out of every field. Reviewers prefer a typo over AI-flattened text, so keep the speaker's own phrasing.

Live-form requirements (confirmed from the Sessionize form on 2026-10-11): the Description (abstract) has a hard limit of 1000 characters. The reviewer-only relevance field is now "Value to the community" (why the talk is important, relevant, and timely), replacing the former "Benefits to the Ecosystem"; no character limit is shown. CNCF and other open source projects are now a single combined field. The bio limit is 500 characters. A Content Quality Agreement warns that AI-generated slop can remove a submission from review and ban the speaker from future CNCF CFPs, so keep the speaker's own phrasing and avoid AI-flattened text.

## Notes

Seeded from brainstorm/research/kubecon-cfp-research.md on 2026-10-09. Co-located Day 0 events, the project benefits CFP (Maintainer Track, Project Lightning Talks, ContribFest), and the Maintainer Summit use separate Sessionize CFPs with different formats and limits; they need their own profiles or event overrides.

2026-10-10: abstract guidance changed to session-centric wording (no speaker or company names in abstract or title, state demos explicitly) after checking accepted abstracts on the KubeCon NA 2025 schedule (kccncna2025.sched.com, Security track).

2026-10-11: updated to the live Sessionize form. Abstract limit 1000 (confirmed), bio 500 (confirmed), benefits replaced by value_to_community, cncf_projects and open_source_projects merged into cncf_oss_projects, track strings aligned to the form (AI Inference + Infrastructure, Platform Engineering: DevEx + IDPs).

2026-10-11: resources field changed to free text (longtext) to match the live form.

2026-10-11: seed updated to the live form (seed_version 2026-10-11); limits confirmed by screenshot are marked `screenshot`, the rest remain `unverified`.
