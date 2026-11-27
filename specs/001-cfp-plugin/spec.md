# Feature Specification: CFP and Bio Plugin for Conference Submissions

> **Historical record.** This specification and the other files in this directory describe the design as of 2026-10-09 and are not kept up to date. The shipped KubeCon profile changed after that date: the abstract limit is 1000, `value_to_community` replaced `benefits`, one `cncf_oss_projects` field replaced the two project fields, and several limits are confirmed by screenshot. For the current behavior read `cfp/knowledge-base/profiles/kubecon/profile.md`, the skills under `cfp/skills/`, and the README.

**Feature Branch**: `001-cfp-plugin`

**Created**: 2026-10-09

**Status**: Draft

**Input**: User description: "Build a Claude Code plugin ("cfp") that drafts conference talk proposals (CFP submissions) and speaker bios interactively, using reusable conference profiles. Talk-centric workflow: conference profile (family + per-event overrides), talk (conference-independent story), proposal (talk rendered for one profile and event, field by field, with lifecycle status), bio variations, speaker resources. Store is markdown in a configurable Obsidian vault folder. Commands: profile research/create/refresh, bio management, interactive proposal drafting with simulated program committee review, prose voice pass, pre-flight rule check and paste view, status update. Ships with a KubeCon seed profile. No auto-submission. Solo speaker focus."

> **Note**: Superseded by feature 002: the default store is `<data folder>/store` and the config folder follows XDG; see specs/002-xdg-config-store/spec.md.

Source documents: `brainstorm/01-cfp-plugin.md` (decision and key requirements) and `brainstorm/research/kubecon-cfp-research.md` (KubeCon formats, fields, rubric, rules).

## Clarifications

### Session 2026-10-09

- Q: Is the pre-flight rule check a step inside the drafting flow or a separate command? → A: Both. It runs automatically before the paste view, and a standalone check command runs it on any stored proposal.
- Q: What happens when the chosen profile has no event override for the target event? → A: The drafting command offers to create the override inline (research via the profile command or minimal manual entry) and continues; it does not block.
- Q: When does a proposal move from draft to ready? → A: Automatically when the committee review verdict is pass and the pre-flight check has no disqualifying findings; the user can also set it manually through the status command.
- Q: Where does configuration live? → A: The store path lives in a small user-level plugin configuration outside the store. Speaker name, voice profile, and review round limit live in a configuration file inside the store.
- Q: How are submission form screenshots supplied to the profile command? → A: As image file paths or as images pasted into the conversation; both are accepted.
- Q: Which proposal statuses count toward the per-event submission limit? → A: submitted, accepted, rejected, presented count; draft, ready, withdrawn do not.
- Q: Where does a bio go after the voice pass or shortening changes it? → A: The proposal stores a snapshot of the bio text plus the variation name; stored variations are never changed by drafting.
- Q: What needs approval before use? → A: Family profile and each event override separately; research-produced overrides require review, manual inline entries are approved by being entered.
- Q: How are over-limit fields handled at the paste view? → A: Drafting offers to shorten any over-limit field before producing the paste view.
- Q: What is the step order after a passing review? → A: Voice pass (counts rechecked, no re-review), then pre-flight, then paste view; ready is set after pre-flight.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Draft a KubeCon proposal from an idea (Priority: P1)

A speaker has a rough talk idea and an upcoming KubeCon CFP deadline. They start the drafting command, pick the KubeCon profile and the concrete event, choose a session type, and describe their idea. The plugin interviews them to extract the talk story (the problem, their contribution, explicit takeaways, target personas, what is new, prior outings), offers two or three candidate title and abstract angles, and after the speaker picks one, drafts every field the event's form requires. A simulated program committee then scores the draft against the conference's published rubric and the speaker revises with the plugin until it passes. The result is a proposal file in the store and a paste view listing each field in form order with its character count.

**Why this priority**: This is the reason the plugin exists. A sub-10-percent acceptance rate at KubeCon makes abstract quality the dominant value, and every other story only supports this one.

**Independent Test**: With the shipped KubeCon profile and no other stored data, a user can run the drafting command with a one-line idea and end with a complete, reviewed proposal and a paste view. Delivers a submission-ready KubeCon proposal.

**Acceptance Scenarios**:

1. **Given** the shipped KubeCon profile and an event with a track list, **When** the user starts drafting, **Then** the plugin asks, one question at a time, for the event, the session type (from the profile's list with duration and speaker limits shown), and the input source, before any text is generated.
2. **Given** the user supplied a one-line idea, **When** story extraction runs, **Then** the plugin asks about the problem, the contribution, concrete takeaways, target personas, what is new compared to existing talks, and prior outings of the same material, and records the answers as a talk in the store.
3. **Given** a complete talk story, **When** angles are generated, **Then** the user sees two or three distinct title and abstract candidates with a one-line note on the hook each uses, and chooses one or asks for another round.
4. **Given** a chosen angle, **When** field drafting runs for KubeCon, **Then** a draft exists for title, abstract, benefits to the ecosystem, audience level, track, case-study flag, previously-presented note, CNCF and open source projects, and additional resources, and the benefits text does not restate the abstract but explains who benefits, why now, and what is new.
5. **Given** drafted fields, **When** the committee review runs, **Then** the user sees a score for each rubric criterion (Content, Originality, Relevance, Speaker, Not a Product Pitch) with a reviewer-style comment per criterion, and a verdict of pass or revise.
6. **Given** a revise verdict, **When** the user accepts the suggested revisions, **Then** the affected fields are rewritten and the review runs again, and the loop ends when the verdict is pass or the user stops it.
7. **Given** a passing draft, **When** the paste view is produced, **Then** every field appears in the order of the event's form with its current character count and the profile's limit, and any field over its limit is flagged.
8. **Given** a passing draft, **When** the voice pass runs, **Then** the prose fields are rewritten through the prose plugin with the user's voice profile and the character counts are rechecked afterwards.

---

### User Story 2 - Maintain bios and speaker resources (Priority: P2)

A speaker keeps several bio variations (short and long, cloud-native emphasis, AI emphasis) and a list of speaker resources (talk recordings, repositories, blog posts, prior conference sessions) in the central store. While drafting a proposal they pick a bio variation and the plugin reports its length against the profile's bio limit. Resources are offered for the proposal's additional resources field because conference reviewers score speakers higher when a recording is linked.

**Why this priority**: Bios and resources are reused across every submission and directly affect the Speaker criterion of the review rubric. Without them, each proposal starts from a blank speaker section.

**Independent Test**: A user with an empty store can create three bio variations and two resources through the bio command, list them, and see each bio's character count. Delivers a reusable speaker identity independent of any proposal.

**Acceptance Scenarios**:

1. **Given** an empty store, **When** the user runs the bio command to create a bio, **Then** the plugin asks for the emphasis and target length, drafts a third-person bio, lets the user edit it, and saves it as a named variation.
2. **Given** several bio variations exist, **When** the user lists them, **Then** each shows its name, emphasis, character count, and last updated date.
3. **Given** bio variations and a profile with a bio limit, **When** the user selects a bio during drafting, **Then** the plugin shows the count against the limit and offers to shorten the bio if it exceeds the limit.
4. **Given** the user adds a speaker resource with a type and link, **When** a proposal reaches the additional resources field, **Then** the stored resources are offered for selection and the recording type is recommended first.

---

### User Story 3 - Create or refresh a conference profile by research (Priority: P3)

A speaker wants to submit to a conference the plugin does not know yet, or an existing profile has drifted from the live form. They run the profile command with the conference name or CFP page link and optionally provide screenshots of the submission form. The plugin researches the public CFP pages, reads the screenshots, and produces a profile draft covering session types, form fields with limits and options, tracks, dates, review criteria, hard rules, and rejection reasons. The user reviews and approves the draft before it becomes usable.

**Why this priority**: The shipped KubeCon profile covers the first use. Research is what makes the plugin work for other conferences and for KubeCon editions whose forms change.

**Independent Test**: A user points the profile command at a public CFP page and ends with an approved profile file that the drafting command accepts. Delivers reuse for any conference without code changes.

**Acceptance Scenarios**:

1. **Given** a conference name or CFP page link, **When** the profile command runs, **Then** the plugin fetches the public CFP pages, extracts session types, fields, tracks, dates, criteria and rules, and presents a draft profile for review with each item marked as verified (with source) or unverified.
2. **Given** screenshots of the submission form, **When** supplied to the profile command, **Then** field labels, option lists, required markers, and character limits visible in the screenshots are added to the draft and marked as verified from the screenshot.
3. **Given** an existing profile and a new event edition, **When** the user runs a refresh for that event, **Then** the plugin creates or updates the per-event override (dates, tracks, session type variations, submission limit) without altering the family profile unless the user approves changes to it.
4. **Given** a draft profile, **When** the user rejects or edits items, **Then** only the approved version is saved and the drafting command refuses to use a profile that was never approved.

---

### User Story 4 - Track proposal lifecycle and reuse past work (Priority: P4)

After submitting, the speaker records the proposal as submitted with the date. When the notification arrives they mark it accepted or rejected, and later presented. Accepted proposals become calibration examples for the profile. A rejected proposal can be reopened as the input to a new proposal for another event or conference, carrying its talk story along.

**Why this priority**: Outcomes are what make the plugin improve over time, and resubmission is how a sub-10-percent acceptance rate is survived. It depends on proposals existing first.

**Independent Test**: A user with one stored proposal can move it through submitted, rejected, and reopen it as input for a new proposal against a different event. Delivers an audit trail and a resubmission path.

**Acceptance Scenarios**:

1. **Given** a proposal in draft status, **When** the user runs the status command and chooses submitted, **Then** the proposal records the status and the submission date, and the pre-flight submission count for that event includes it.
2. **Given** a submitted proposal, **When** the user marks it accepted, **Then** its title, abstract, and benefits text are added to the profile's calibration examples with the event and year.
3. **Given** a rejected proposal, **When** the user starts a new proposal and selects it as the input source, **Then** the talk story is loaded, the previous abstract is shown for reference, and the previously-presented rule check treats the rejected proposal as not presented.
4. **Given** several proposals, **When** the user lists them, **Then** each shows its title, profile, event, status, and relevant date, grouped by status.

---

### User Story 5 - Pre-flight rule check before submission (Priority: P5)

Before pasting a proposal into the submission site, the speaker runs the pre-flight check. The plugin verifies the hard rules recorded in the profile: number of proposals already submitted to the event, whether the same talk was presented at the conference family within the past year, whether the chosen track exists for the event, whether the stated audience level matches the content, and whether session type speaker counts and composition rules are respected. Violations are listed with the rule source.

**Why this priority**: Rule violations disqualify a proposal regardless of quality. The check is cheap but only meaningful once drafting and status tracking exist.

**Independent Test**: With a profile containing rules and two stored submitted proposals for an event, a third proposal triggers the submission limit warning when the limit is three and a fourth is drafted. Delivers protection against disqualification.

**Acceptance Scenarios**:

1. **Given** the KubeCon profile with a limit of three proposals per event and three proposals already submitted to that event, **When** pre-flight runs on a fourth, **Then** the plugin reports the limit violation and cites the rule.
2. **Given** a talk marked as presented at a KubeCon event within the last twelve months, **When** pre-flight runs on a proposal of that talk for another KubeCon event, **Then** the plugin warns about the repeat rule and asks whether the previously-presented note explains significant differences.
3. **Given** a proposal whose track is not in the event's track list, **When** pre-flight runs, **Then** the plugin reports the mismatch and offers the event's list.
4. **Given** a proposal whose abstract uses advanced terminology but is labeled beginner, **When** pre-flight runs, **Then** the plugin flags the level mismatch with a short reason.

---

### Edge Cases

- The store folder does not exist or is not configured: the plugin asks for the path on first use, creates the folder structure, and records the configuration.
- A profile has no character limit for a field: the paste view shows the count without a limit and the review uses the profile's guidance only.
- Limits in a profile are marked unverified (as for the shipped KubeCon profile): the paste view labels the limit as approximate and warns that the live form may differ.
- The user supplies existing material (blog post, slides, repository link) as input: the plugin reads it, proposes the talk story from it, and asks only for what the material does not cover.
- The user stops mid-draft: the talk and the partial proposal are saved as draft and the drafting command offers to resume them next time.
- The committee review never reaches a pass verdict after several rounds: the loop stops after a configurable number of rounds (default three) with the remaining weaknesses listed, and the user decides whether to continue, accept as is, or park the proposal.
- Research for a profile finds nothing public (login-walled form, no CFP page): the plugin produces a minimal profile from what the user tells it, marks everything unverified, and suggests screenshots.
- Screenshots contradict the public pages: screenshot values win and the conflict is noted in the profile.
- An event's CFP deadline has passed: the drafting command warns but still allows drafting (for a future edition or as practice).
- The chosen profile has no override for the target event: the drafting command offers inline creation (research or minimal manual entry) and continues.
- The prose plugin is not installed: the voice pass is skipped with a notice and the texts remain as drafted.
- A stored file has invalid or missing front matter after a manual edit: the plugin reports the file path and the problem, skips that file, and continues with the rest of the store.
- A talk is reused for a co-located event of the same family with different field limits: the proposal is re-rendered against the co-located event's fields and limits, not the main CFP's.

## Requirements *(mandatory)*

### Functional Requirements

**Store and configuration**

- **FR-001**: The plugin MUST keep all data (profiles, talks, proposals, bios, resources, store configuration) as plain markdown files with structured front matter in a user-configurable folder, defaulting to a folder inside the user's Obsidian vault. (Superseded by feature 002: the default store is `<data folder>/store` and the config folder follows XDG; see specs/002-xdg-config-store/spec.md.)
- **FR-002**: The plugin MUST work for any speaker without code changes: the speaker's name, voice profile, review round limit, and store path MUST be configuration, not fixed values.
- **FR-002a**: The store path MUST be kept in a user-level plugin configuration outside the store; the speaker name, voice profile, and review round limit MUST be kept in a configuration file inside the store so they travel with the data.
- **FR-003**: Every stored file MUST remain readable and editable by hand, and the plugin MUST tolerate manual edits that keep the front matter valid.

**Conference profiles**

- **FR-004**: A profile MUST describe a conference family and contain: submission platform, session types (name, duration, minimum and maximum speakers), submission limits, an ordered list of form fields (label, required flag, character limit, limit verification status, option list, drafting guidance, whether the field is public or reviewer-only), a review rubric with named criteria, scale, and pass threshold, hard disqualification rules, common rejection reasons, and calibration examples of accepted texts. A verification status MUST be one of: unverified, verified from a public page (with the source link), or verified from a screenshot.
- **FR-005**: A profile MUST support per-event overrides that record the event name, location, event dates, CFP open and close dates, notification date, track list, session type variations, and submission limit for that edition, and the drafting command MUST apply the override on top of the family profile.
- **FR-006**: The plugin MUST ship with a KubeCon + CloudNativeCon profile built from the research document, including at least the EU 2027 and NA 2026 event overrides, the five-criterion reviewer rubric, the hard rules (three-proposal limit, one-year repeat rule, all-men session rule for three or more speakers, panel company rule, vendor pitch rule), and the historic character limits marked as unverified. The shipped profile MUST be marked approved so drafting works without a prior review step.
- **FR-007**: The profile command MUST accept a conference name or CFP page link, research the public CFP pages, and produce a profile draft where each item carries a source or an unverified marker.
- **FR-008**: The profile command MUST accept one or more screenshots of a submission form, supplied as image file paths or as images pasted into the conversation, and extract field labels, order, required markers, option lists, and character limits from them, marking those items as verified from the screenshot.
- **FR-009**: The profile command MUST present the draft for review and save only the approved version; a profile that has never been approved MUST NOT be usable for drafting. Approval is tracked separately for the family profile and for each event override: overrides produced by research MUST be reviewed before use, while an override entered manually by the user counts as approved by the act of entering it.
- **FR-010**: The profile command MUST support refreshing an existing profile for a new event edition by creating or updating that event's override, and MUST ask before changing the family profile.
- **FR-010a**: When the drafting command targets an event that has no override in the chosen profile, it MUST offer to create the override inline, either by running the profile refresh (research) or by minimal manual entry of name, dates, tracks, and limits, and MUST continue drafting afterwards rather than block.

**Talks**

- **FR-011**: A talk MUST capture a conference-independent story: working title, problem, contribution, explicit takeaways, target personas, what is new, projects involved, prior outings (event, date, link), and linked speaker resources.
- **FR-012**: The drafting command MUST build or update a talk from any of four input sources: a one-line idea through an interview, existing material (text, link, or file the user provides) with an interview for the gaps, an existing talk from the store, or an existing proposal.

**Proposal drafting**

- **FR-013**: The drafting command MUST be interactive and ask one question at a time, offering choices where the profile defines them (session type, track, audience level, bio variation, resources).
- **FR-014**: The drafting command MUST show the session type's duration and speaker limits when the user chooses it, and MUST refuse session types whose speaker rules the solo speaker cannot satisfy unless the user confirms co-speakers exist.
- **FR-015**: The drafting command MUST generate two or three distinct candidate title and abstract angles from the talk story and let the user pick one or request another round.
- **FR-016**: The drafting command MUST draft every field the event's form defines, using the field's drafting guidance, limit, and option list from the profile.
- **FR-017**: When a profile defines a reviewer-only relevance field (such as KubeCon's benefits to the ecosystem), the drafted text MUST address who benefits, why now, and what is new, and MUST NOT restate the abstract.
- **FR-018**: The drafting command MUST run a simulated program committee review that scores the draft on each rubric criterion of the profile with a reviewer-style comment per criterion and a verdict of pass or revise.
- **FR-019**: The review MUST treat the profile's rejection reasons and calibration examples as reference: generic phrasing, vendor pitch signals, missing takeaways, and AI-sounding text MUST lower the relevant criterion scores.
- **FR-020**: After a revise verdict the drafting command MUST propose concrete rewrites for the weak fields, apply them on acceptance, and re-run the review, stopping after a configurable number of rounds (default three) or when the user stops.
- **FR-021**: The drafting command MUST run the final prose fields (title, abstract, reviewer-only relevance field, bio) through the prose plugin's humanizer with the configured voice profile, and MUST skip this step with a notice when the prose plugin is unavailable. The voice pass runs after a passing review verdict, rechecks character counts afterwards, and does not trigger a second review.
- **FR-021a**: The steps after a passing review verdict MUST run in this order: voice pass, pre-flight check, paste view. The proposal becomes ready only after the pre-flight check succeeds (see FR-031a).
- **FR-022**: The drafting command MUST produce a paste view listing every field in the form's order with the drafted text, its character count, the profile's limit, and a flag when the count exceeds the limit or the limit is unverified. Before producing the paste view, the drafting command MUST offer to shorten any field whose count exceeds a known limit, so that a paste view normally contains no over-limit fields.
- **FR-023**: The drafting command MUST save the talk and the proposal to the store at every step, so an interrupted session can be resumed.

**Bios and resources**

- **FR-024**: The bio command MUST create, list, edit, and delete bio variations, each with a name, emphasis, target length, third-person text, and character count.
- **FR-025**: The bio command MUST manage speaker resources, each with a type (recording, repository, blog post, prior session, publication, other), a title, a link, and an optional date.
- **FR-026**: During drafting, the plugin MUST let the user pick a bio variation, show its count against the profile's bio limit, and offer to shorten it when over the limit. The proposal stores its own snapshot of the bio text together with the variation name; shortening and the voice pass change only the snapshot, never the stored variation.
- **FR-027**: During drafting, the plugin MUST offer stored resources for the form's resources field and recommend a recording when the profile's rubric rewards presentation evidence.

**Pre-flight rule check**

- **FR-028**: The pre-flight check MUST evaluate the profile's hard rules against the store: proposals already submitted to the same event, the same talk presented at the same conference family within the past twelve months, track membership in the event's track list, session type speaker counts, and composition rules. For the per-event submission limit, proposals with status submitted, accepted, rejected, or presented count; draft, ready, and withdrawn do not.
- **FR-028a**: The pre-flight check MUST run automatically inside the drafting flow before the paste view is produced, and MUST also be available as a standalone check command that runs on any stored proposal.
- **FR-029**: The pre-flight check MUST flag an audience level that does not match the content of the abstract, with a short reason.
- **FR-030**: Every pre-flight finding MUST cite the rule it comes from and state whether it disqualifies the proposal or is a warning. Findings from the profile's hard disqualification rules disqualify; the audience level mismatch (FR-029) and the one-year repeat rule when a previously-presented note exists are warnings.

**Lifecycle**

- **FR-031**: Each proposal MUST carry a status from the set draft, ready, submitted, accepted, rejected, withdrawn, presented, plus the event and the dates of submission, decision, and presentation where known.
- **FR-031a**: A proposal MUST move from draft to ready automatically when the committee review verdict is pass and the pre-flight check reports no disqualifying findings; the status command MUST also allow setting ready manually.
- **FR-032**: The status command MUST let the user change a proposal's status and record the date, and MUST list proposals grouped by status.
- **FR-033**: When a proposal becomes accepted, the plugin MUST add its title, abstract, and reviewer-only relevance text to the profile's calibration examples with the event and year.
- **FR-034**: When a proposal becomes presented, the plugin MUST record the outing on its talk so the one-year repeat rule applies to future proposals of that talk.
- **FR-035**: A rejected or withdrawn proposal MUST be selectable as the input source for a new proposal, carrying its talk story.

**Out of scope**

- **FR-036**: The plugin MUST NOT submit anything to a conference website or interact with the submission site on the user's behalf.
- **FR-037**: The plugin MUST NOT manage co-speaker bios or profiles; co-speaker details are free text on the proposal.
- **FR-038**: The plugin MUST NOT generate slides, speaker notes, or any post-acceptance material.

### Key Entities

- **Profile**: A conference family's knowledge: platform, session types, ordered form fields with limits and guidance, review rubric, hard rules, rejection reasons, calibration examples. Approved status. Has many event overrides.
- **Event override**: One edition of a conference family: name, location, dates, CFP window, notification date, track list, session type variations, submission limit. Approved status of its own. Belongs to one profile.
- **Talk**: A conference-independent story: working title, problem, contribution, takeaways, personas, what is new, projects, prior outings, linked resources. Has many proposals.
- **Proposal**: One talk rendered for one profile and event: chosen session type, chosen angle, one drafted value per form field, chosen bio variation name plus a snapshot of its text, chosen resources, review history (scores and comments per round), status and dates. Belongs to one talk and one event.
- **Bio variation**: A named third-person bio with emphasis, target length, text, and character count.
- **Speaker resource**: A reusable link with type, title, date; offered for resources fields and used as presentation evidence.
- **Configuration**: Two parts. User-level plugin configuration holding the store path. Store configuration holding speaker name, voice profile name, and review round limit.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user with a one-line idea reaches a complete, reviewed KubeCon proposal with a paste view in a single session of at most 30 minutes of interaction.
- **SC-002**: Every proposal that reaches the paste view has all required fields of the event's form filled, and 100 percent of fields with a known limit are at or under that limit.
- **SC-003**: The simulated committee review reports a score and comment for every criterion of the profile's rubric on every round, with no criterion left unscored.
- **SC-004**: A second proposal from an existing talk for a different event (for example a co-located event) is produced in under 10 minutes of interaction, reusing the stored story, bio, and resources without re-entering them.
- **SC-005**: Running the profile command against a public CFP page yields a draft where at least the session types, required fields, and dates are filled, and every item is labeled verified or unverified.
- **SC-006**: The pre-flight check catches 100 percent of the hard rules encoded in the profile when tested with proposals that violate each rule one at a time.
- **SC-007**: After marking a proposal accepted, its texts appear in the profile's calibration examples and are offered as reference in the next drafting session for that profile.
- **SC-008**: All stored files open and render correctly in Obsidian and can be edited there without breaking subsequent plugin runs.

## Assumptions

- The user runs the plugin inside Claude Code with the prose plugin installed for the voice pass; when it is missing, the voice pass is skipped rather than failing.
- The shipped KubeCon profile uses the historic character limits (title 75, abstract 1,300, benefits 1,000, bio 500) as unverified soft limits until the user confirms them with screenshots of the live form.
- The committee review's pass threshold defaults to an average of at least 4 of 5 across criteria with no criterion below 3, mirroring the top-30-percent cut reviewers apply; the threshold is stored in the profile and can be tuned.
- Review scores are numeric on the profile's scale with a comment per criterion, because the KubeCon rubric is star-based; profiles with qualitative criteria use pass or revise per criterion.
- Calibration examples start with the public sample submission from the Linux Foundation CFP page and the user's own accepted proposals. Harvesting accepted abstracts from published conference schedules is explicitly deferred to a later version; the profile format leaves room for manually added examples in the meantime.
- Existing material supplied as input is text the user pastes, a local file path, or a public link; private documents behind logins are out of scope.
- One store serves one speaker. Multiple speakers use separate stores.
- Dates and deadlines are informational; the plugin does not send reminders.
- Co-speakers can exist on a proposal as free-text names and affiliations so that panel and tutorial rules can be checked, but their bios are not managed.
