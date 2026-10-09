# Brainstorm: CFP and Bio Plugin for Conference Submissions

**Date:** 2026-10-09
**Status:** spec-created (specs/001-cfp-plugin)
**Research:** [research/kubecon-cfp-research.md](research/kubecon-cfp-research.md)

## Problem Framing

Submitting talks to conferences is repetitive, form-driven work with a high bar. The same speaker submits to the same conference families year after year (KubeCon EU, KubeCon NA, co-located days), each time re-discovering the form fields, their limits, the track list, and the unwritten selection criteria. Bios are rewritten from scratch or copied from an old submission. Abstracts are drafted in a hurry and compete against thousands of others.

KubeCon makes the quality problem acute. Acceptance has fallen from about 17 percent in 2018 to 8 to 11 percent in 2024 and 2025, with roughly 90 slots per event reserved for the Maintainer Track and never entering the open pool. Reviewers score on a public rubric (Content, Originality, Relevance, Speaker, plus a "Not a Product Pitch" gate) where the one-star anchors explicitly name "AI slop". The "benefits to the ecosystem" field is officially the second determining factor and is reviewer-only. Hard rules disqualify regardless of quality: more than three proposals, a repeat of a talk given at a Linux Foundation event in the past year, sessions of three or more speakers who all identify as men, wrong track.

The plugin should turn this into a guided, interactive process: know the form in advance, reuse what does not change (bios, speaker resources, the talk's story), and push every abstract toward the top of the reviewer pile. No auto-submission; the output is paste-ready text per field.

## Context Gathered

Research into KubeCon + CloudNativeCon CFPs (see linked research document) established:

- Session types and limits vary by edition and by CFP (main, co-located, project benefits). Track lists change every edition.
- The Linux Foundation CFP pages describe all fields but state no character limits. Historic limits: title 75, abstract 1,300, benefits 1,000, bio 500 to 800 characters. The live Sessionize form sits behind a login wall.
- The Speaker score depends on linking a recording of a previous talk, so speaker resources are as reusable as bios.
- Co-chairs emphasize the full story, the hard parts, lessons learned, explicit takeaways, the right track, and specific value in the first two sentences.

User decisions during the session:

- Store lives in the Obsidian vault as markdown, path configurable.
- Full proposal lifecycle is tracked (draft, submitted, accepted, rejected, presented).
- Solo speaker focus; co-speaker details stay free text.
- Inputs can be a one-liner, existing material (blog post, slides, repo, earlier talk), or a previous proposal.
- Quality mechanisms: simulated program committee review against the real rubric, two or three candidate angles, calibration from accepted examples, and a voice pass via the prose plugin.
- Profiles are per conference family with per-event overrides.

## Approaches Considered

### A: Talk-centric workflow (chosen)

The core entity is a *talk*: the conference-independent story (problem, contribution, takeaways, audience, resources, prior outings). A *proposal* is that talk rendered for one profile and one event, field by field. Commands mirror the speaker's journey: profile research and refresh, bio management, interactive drafting, committee review, status update.

- Pros: Resubmission is natural (a rejected KubeCon talk becomes a co-located event proposal or another conference's submission quickly). Abstract and benefits are drafted from one shared story, so they stay consistent without duplicating each other. Accepted talks become calibration material automatically.
- Cons: Two concepts (talk and proposal) to explain. Slightly more upfront modeling.

### B: Form-centric generic filler

The profile is purely a form schema: ordered fields, limits, options, per-field guidance. Drafting walks the schema and generates each field. KubeCon is one schema with extra fields and a rubric attached.

- Pros: Simplest mental model, generalizes to any conference, profile research maps directly to form fields.
- Cons: Field-by-field drafting produces disconnected text. Committee review and angle selection have no shared story to work on. Reuse across conferences is copy and paste.

### C: KubeCon-only first, generalize later

Hardcode KubeCon's structure and rubric into the drafting command, build the quality loop well, extract profiles once a second conference appears.

- Pros: Fastest path to a strong KubeCon abstract. No speculative generality.
- Cons: Contradicts the explicit profile requirement. The second conference forces a refactor. The research command has nowhere to put its output.

## Decision

Approach A, talk-centric workflow. The talk entity is what makes the quality mechanisms work: angle generation, committee review, and calibration all need the underlying story rather than isolated form fields. It also gives the resubmission path that a sub-10-percent acceptance rate makes necessary.

## Key Requirements

### Store

- Central store in the Obsidian vault under a configurable folder, plain markdown with frontmatter.
- Holds conference profiles, talks, proposals, bios, and speaker resources (talk recordings, repos, blog posts, prior KubeCon sessions).
- Nothing about the person is hardcoded; the plugin is publishable via the cc-* marketplace pattern.

### Conference profiles

- A profile describes a conference family (first: kubecon): the CFP platform, session types with duration and speaker limits, submission limits, every form field with required flag, soft character limit, option list, and drafting guidance, the reviewer rubric and known selection criteria, hard disqualification rules, common rejection reasons, and example accepted abstracts for calibration.
- Per-event overrides record what changes per edition: event name, dates (CFP open and close, notification), track list, session type variations, submission limit.
- A profile command researches a conference's public CFP pages and accepts form screenshots (Sessionize, Sched) to produce or refresh a profile draft. The user reviews and approves before use.
- A KubeCon seed profile ships with the plugin, built from the 2026-10-09 research, so the first run needs no research round.

### Bios

- A bio command creates and maintains several variations organized by length and emphasis (for example short, long, cloud-native focus, AI focus), written in third person.
- At drafting time the user selects a variation; the plugin reports its character count against the profile's bio limit.

### Interactive drafting

- The drafting command asks step by step: which profile and event, which session type, what input (one-liner, existing material, previous proposal).
- It extracts or updates the talk story: problem, contribution, explicit takeaways, target personas, what is new, prior outings, resources.
- It offers two or three candidate title and abstract angles (for example problem-first, story-driven, contrarian) and the user picks one.
- It drafts every field the profile requires. For KubeCon: title, abstract, benefits to the ecosystem (distinct from the abstract: who benefits, why now, what is new), audience level, track, case-study flag, previously-presented note, CNCF and open source projects, additional resources.
- It runs a simulated program committee review against the profile's rubric, reports weaknesses per criterion, and revises until the draft passes, with the user in the loop.
- It runs the final texts through the prose plugin with the user's voice profile.
- It runs a pre-flight rule check: submission count for the event, repeat-within-a-year, track fit, level match to content, panel composition rules.
- It produces a paste view: fields in form order, each with its character count against the limit.

### Lifecycle

- Each proposal carries a status: draft, submitted, accepted, rejected, presented, plus the event and submission date.
- A status command updates it. Accepted proposals are added to the profile's calibration examples. Rejected proposals can be reopened as input for a new proposal.

### Out of scope (first iteration)

- Auto-submission to Sessionize or any site.
- Managing co-speaker bios beyond free text.
- Slides, speaker notes, post-acceptance work.
- Shipped profiles for conferences other than KubeCon (the research command covers them).

## Open Questions

- Exact current KubeCon character limits and Sessionize question labels. The KubeCon EU 2027 form is live until 2026-10-11; screenshots of it would settle title, abstract, benefits, and bio limits plus the optional speaker-level questions.
- How many public accepted abstracts to include as calibration examples and how to keep them current per edition.
- Whether the committee review produces numeric star scores per criterion or a qualitative verdict only.
- Vault folder layout and naming for talks, proposals, profiles, bios, and resources.
- How per-event overrides are created: automatically from research or manually per event.
- Whether the prose voice pass should run on the abstract only or also on the reviewer-only benefits field.
