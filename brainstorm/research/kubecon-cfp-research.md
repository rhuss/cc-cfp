# KubeCon + CloudNativeCon CFP Requirements: Research Report

Date: 2026-10-09

## Summary

KubeCon + CloudNativeCon runs all calls for proposals (CFPs) on Sessionize, with a near-identical field set across the Europe, North America, Japan, China, and India editions: title, session description, benefits to the ecosystem, case study flag, previously-presented explanation, project list, additional resources, audience level, track, and format, plus the standard Sessionize speaker profile (name, company, job title, bio, photo, links) and co-speaker invitations. Session formats for the main CFP are a 30-minute session (1-2 speakers), a 30-minute panel (3-5), a 5-minute lightning talk (1), a 75 or 80-minute tutorial (1-5), and a poster session (1-2). Submitters may be listed on at most three proposals and can be selected for at most one panel and one non-panel session. Reviewers score on a public 1-5 star rubric (Content, Originality, Relevance, Speaker, plus a Not-a-Product-Pitch gate), and the LF pages state that the "benefits to the ecosystem" answer is the second determining factor after the abstract. Acceptance has fallen from about 17% in 2018 to 8% for Europe 2025. The biggest gap in this research is that the live Sessionize form sits behind a login wall, so current character limits and exact question labels could not be verified; all limits quoted here come from older forms and community templates.

## 1. Session types and formats

### Main KubeCon CFP

Identical across EU 2027, NA 2026, Japan 2026, China 2026, EU 2026, and NA 2025, except tutorial length.

| Format | Duration | Speakers | Notes |
|---|---|---|---|
| Session Presentation | 30 min | 1-2 | |
| Panel Discussion | 30 min | 3-5 | All participants named at submission |
| Lightning Talk | 5 min | max 1 | |
| Tutorial | 80 min (EU 2027), 75 min (all others) | 1-5 | Hands-on |
| Poster Session | none (digital poster at a monitor in the Solutions Showcase) | 1-2 | EU 2027, NA 2026, NA 2025 only; submitted via the regular CFP as format "Poster Session"; counts toward the 3-proposal limit; research-focused or novel work encouraged; presenters staff the booth during KubeCrawl |

Limits:

- Max 3 proposals per speaker in any format. Exceeding this "may result in all proposals being removed from review," including those with co-speakers. (NA 2025 Sessionize page said 2; all 2026 and later pages say 3.)
- Selected for at most 1 panel and 1 non-panel session per event, excluding project benefits.
- Keynotes: no keynote submission type exists on any CFP page. The 2020 scoring guidelines mention reviewers flagging "keynote-worthy" talks, and the OpenSSF podcast speakers report an accepted 25-minute talk being moved to a keynote slot. Unverified whether this still happens routinely.

Sources:

- https://events.linuxfoundation.org/kubecon-cloudnativecon-europe/program/cfp/
- https://events.linuxfoundation.org/kubecon-cloudnativecon-north-america/program/cfp/
- https://events.linuxfoundation.org/kubecon-cloudnativecon-japan/program/cfp
- https://www.lfopensource.cn/kubecon-cloudnativecon-openinfra-summit-pytorch-conference-china/program/call-for-proposals-cfp/
- https://events.linuxfoundation.org/archive/2026/kubecon-cloudnativecon-europe/program/cfp/
- https://events.linuxfoundation.org/archive/2025/kubecon-cloudnativecon-north-america/program/cfp/

### CNCF-hosted co-located events (Day 0)

EU 2027 has 14 events: Agentics Day: MCP + Agents, ArgoCon, BackstageCon, Buildpacks Summit, CiliumCon, Cloud Native AI + Inference Day, FluxCon, KeycloakCon, Kubernetes on Edge Day, Observability Day, Open Sovereign AI + Cloud Day, Open Source SecurityCon, OpenTofu Day, Platform Engineering Day. NA 2026 has 11 (no Buildpacks Summit, KeycloakCon, Open Sovereign AI + Cloud Day). Separate Sessionize CFP.

| Format | Duration | Speakers |
|---|---|---|
| Solo Presentation (NA page: "Session Presentation") | 25 min | 1 (NA: 1-2) |
| Dual Presentation | 25 min | 2 |
| Panel Discussion | 35 min | 3-5 |
| Lightning Talk | 10 min | max 1 |

No tutorials or posters. Limit: 1 panel and 1 non-panel per co-located event. The EU 2026 co-located page stated a maximum of two proposals per co-located event and ten in total across all co-located events; not confirmed on the EU 2027 page.

Sources:

- https://events.linuxfoundation.org/kubecon-cloudnativecon-europe/co-located-events/cfp-colocated-events/
- https://events.linuxfoundation.org/kubecon-cloudnativecon-north-america/co-located-events/cfp-colocated-events/
- https://sessionize.com/cncf-hosted-co-located-events-europe-2027/

### Project benefits (Maintainer Track, Project Lightning Talks, ContribFest)

Separate Sessionize CFP with restricted eligibility. These do not count toward the main CFP speaker limits.

| Format | Duration | Speakers | Eligibility |
|---|---|---|---|
| Maintainer Track | 30 min | up to 5, each speaker in only one session, one session per project/SIG/TAG | Submitter must be a listed maintainer at maintainers.cncf.io of a graduated or incubating project, or a TAG chair/tech lead, Kubernetes SIG lead, CNCF or Kubernetes Working Group lead. Sandbox not eligible. Speakers need not be maintainers but should be contributors. |
| Project Lightning Talk | 5 min | max 1 (Japan page); EU 2027 page says "You may only speak in two project lightning talks" | Graduated, incubating, sandbox, TAG leads, SIG/WG leads. No complimentary pass. |
| ContribFest | 75 min | max 4, at least one with commit bit | Graduated and incubating only |

Sources:

- https://events.linuxfoundation.org/kubecon-cloudnativecon-europe/features-add-ons/project-opportunities
- https://sessionize.com/kccncjapan-projectlt-maintainer-track/
- https://sessionize.com/project-benefits-kubecon-eu-2026/

### Maintainer Summit

Day before KubeCon. Separate Sessionize CFP. Categories: Growing Contributors, CI/CD/Distribution, Main Track, Project Meetings. Eligibility: TOC representative, graduated project maintainer or org member, TAG chair/technical lead/WG lead, incubating project maintainer. Durations not listed. EU 2027: CFP 23 Sep to 1 Dec 2026, notify 5 Jan 2027, event 14 Mar 2027.

Source: https://sessionize.com/maintainer-summit-eu-2027/

## 2. Form fields

Important caveat: the Sessionize submission form is not publicly visible. The event page shows only the description, and the submit action redirects to `/login?returnUrl=...` (verified with curl on 2026-10-09). The LF CFP pages describe the fields in prose but state no character limits. Limits below come from the NA 2020 form, a 2022 community template, the 2023 co-located CFP PDF, the Akri 2023 draft, and the tracypholmes gist.

R = described as required or expected on the current LF pages; O = optional; H = historic field, current existence unverified.

### Session fields

| Field | Status | Guidance from current LF pages | Historic limit |
|---|---|---|---|
| Session title | R | Title case. Must follow the LF Inclusive Language Initiative. Accurately reflect the talk; it is the public schedule title. | 75 chars (2022 template, 2023 PDF, Akri 2023, gist) |
| Session description (abstract) | R | Emphasize the problem, your contribution, and its relevance. Technical detail without losing the big picture. Full sentences, no bullet lists. Third person (name instead of "I"). Spell-checked, concise. Published verbatim on the schedule if accepted. | 900 (NA 2020), 1,000 (2022 template), 1,300 (2023 PDF, Akri, gist). Best guess 1,300. |
| Benefits to the ecosystem | R | "Explain how your content will benefit the ecosystem or share any other relevant information with the co-chairs and program committee." Reviewer-only. "The relevance of your presentation is just as important as the content and that second determining factor in acceptance." | 1,500 (NA 2020), 1,000 (NA 2021, 2022 template, 2023 PDF, Akri, gist). Best guess 1,000. |
| Case study (yes/no) | R | "A report on an organization's real-world implementation of a practice, product, system, service, or combination thereof, and how well it worked." | |
| Previously presented | R | If given at a CNCF or LF event within the past year, explain significant differences "in your session description." Talks presented at an LF event within the past year are not selected. The 2023 PDF had separate fields: "When did the presentation take place (year, month)" and "link to the slides and/or video of the previous presentation." | |
| CNCF-hosted software | R | "List all CNCF-hosted graduated, incubating, or sandbox software(s) your presentation will be focused on." Historically a multi-select or list. | |
| Open source projects | R | All open source projects discussed, with links. | |
| Additional resources | O, effectively important | "Please provide a video or audio recording of a previous talk you've given. If you don't have one, simply create a quick YouTube video of yourself speaking for a couple of minutes." 2023 PDF: up to 3 resources, each with a type (Presentation Recording, Published Book, Personal Website, Open Source Project, Other) and a link. Poster submitters link published papers here. Reviewer rubric gives 5 stars on Speaker only with "recorded examples of engaging talks." | |
| Audience level | R | Historic label "Level of Expertise for Intended Audience" with options Any/Anyone, Beginner, Intermediate, Advanced. Reviewer guidelines confirm a level is indicated and may be corrected. | |
| Track | R | Single select from the track list (section 3). LF says the list is "a rough guideline." | |
| Session format | R | Single select from section 1. | |
| Audience (free text) | H | "Describe who the audience is and what you expect them to gain." Only in the tracypholmes gist. | none |
| Tutorial extras | H | Learning outcomes, prerequisites, materials to bring (NA 2020 form). | |
| Agreements | R | Code of Conduct; data-sharing consent (Sessionize standard). 2023 PDF also had: commitment to review inclusivity materials; submission is final (title and abstract editable after acceptance); slide deadline agreement. | |

### Speaker fields

Sessionize profile (reused across events): name, company, job title, bio, tagline, photo, email, links. Name, company, job title, bio, and photo appear on the public schedule. Co-speakers are invited by email and must complete their own profile. Panels must name all participants at submission. Submitting on someone else's behalf is allowed via Sessionize agent mode.

Historic per-speaker questions (2022 template, 2023 PDF), current existence unverified:

- Preferred pronouns
- Country of residence
- Employed at an end user company? (yes/no). The current LF page still defines "end user company" and links the CNCF landscape end-user list, so this question likely still exists.
- Has the speaker spoken at any KubeCon + CloudNativeCon before? (yes/no, with session name, date, location, recording link)
- Gender identity: Woman / Man / Other Gender Identity / Prefer not to answer
- Person of color: Yes / No / Prefer not to answer, plus racial/ethnic background multi-select (Asian, Black, Hispanic/Latino, Indigenous Peoples, Pacific Islander, Prefer not to answer, Self-identify)
- Identifies with other underrepresented group(s)
- Twitter/X handle, GitHub handle, other social (LinkedIn)

Diversity questions are marked optional and confidential. No "first-time speaker" checkbox was found, although reviewers target first-time speakers (section 9).

Sources:

- https://events.linuxfoundation.org/kubecon-cloudnativecon-europe/program/cfp/
- https://events.linuxfoundation.org/kubecon-cloudnativecon-north-america/program/cfp/
- https://events.linuxfoundation.org/wp-content/uploads/2023/01/CNCF-hosted-Co-located-Events-Europe-2023-CFP-1.pdf
- https://hackmd.io/b7Pf9w_vTmCcys9V-S62NA
- https://gist.github.com/tracypholmes/4f6b6171709d4f7077de5b2136bf411f
- https://hackmd.io/@akri/ByC58xpDj
- https://events.linuxfoundation.org/archive/2020/kubecon-cloudnativecon-north-america/program/cfp/
- https://sessionize.com/playbook/submit-your-session-for-an-event
- https://sessionize.com/playbook/agent-mode

## 3. Track list

Tracks change every edition. A tool should keep them configurable per event.

EU 2027 (13): Agentic AI; AI Inference and Infrastructure; Cloud Native Application Development; Cloud Native Experience; Cloud Native Novice; Connectivity; Data Processing + Storage; Emerging + Advanced; Observability; Operations + Performance; Platform Engineering: DevEx & IDPs; Platform Engineering: Infrastructure & Delivery; Security.

NA 2026 (11): AI Inference + Agentic; Application Development + Delivery; Cloud Native Experience; Cloud Native Novice; Connectivity; Data Processing + Storage; Emerging + Advanced; Observability; Operations + Performance; Platform Engineering; Security.

Japan 2026, EU 2026, NA 2025 (11): AI + ML; Application Development; Cloud Native Experience; Cloud Native Novice; Connectivity; Data Processing + Storage; Emerging + Advanced; Observability; Operations + Performance; Platform Engineering; Security.

China 2026 (11 "Suggested Topics"): AI + ML + Agentic AI + Data Systems; AI Infrastructure + Accelerators + Performance Engineering; Platform Engineering + Cloud Native Architecture; Application Development + Developer Experience; Operations + Observability + Reliability; Security + Privacy + Trusted Computing; Networking + Edge + Distributed Systems; Cloud Infrastructure + Virtualization + Storage; Emerging Technologies + Research + Advanced Topics; Community + Open Source + Getting Started; Hardware Enablement + Diversification.

Co-located events: pick one event, then a topic from that event's list (for example ArgoCon had 12 topics in 2023).

Sources: the CFP pages listed in section 1.

## 4. Review criteria and rules

### Stated rules on every CFP page

- No sales or marketing pitches. Unlicensed or potentially closed-source technologies are "almost always rejected."
- "CNCF does not accept any session with three or more speakers who all identify as men." Applies to panels and tutorials.
- Panelists must represent more than one company (main CFP). Co-located events require at least three organizations, moderator included.
- AI use is not banned (noted as helpful for non-native English speakers), but low-quality or clearly AI-generated submissions are "strongly discouraged"; repeat offenders may be removed from review or banned from future CFPs.
- Titles must follow the LF Inclusive Language Initiative.
- Talks presented at an LF event within the past year are not selected.
- Accepted speakers must submit slides before the event and follow the Code of Conduct. The LF Inclusive Speaker Orientation course is recommended.

### Reviewer process (EU 2027 Submission Reviewer Guidelines)

- Program committee members score in Sessionize star-rating mode. Top roughly 30% go to two track chairs per track, who approve roughly 30% for co-chairs. EU 2027 timeline: PC review 13-25 Oct, track chairs 26 Oct to 6 Nov, co-chairs 16-27 Nov, schedule 9 Dec.
- A comment is mandatory on every proposal; "LGTM" is not acceptable, because rejected submitters can request feedback.
- Reviewers check that the stated audience level matches the content, flag wrong-track submissions, and note speakers on more than one session plus one panel.
- Panels: diversity of panelists and organizations including moderator, cohesion, fits 35 minutes, sample questions included, relevance of experience, impact if one or two panelists drop out. Ideal panel "talks 80% of the time with 20% audience interaction."
- Conflicts of interest: skip proposals from close colleagues or competitors; review as a KubeCon representative, not for your company.
- Program committee is selected for gender, geographic, company, and project diversity.

The scoring rubric itself is in section 9b.

Sources:

- https://events.linuxfoundation.org/kubecon-cloudnativecon-europe/program/submission-reviewer-guidelines/
- https://events.linuxfoundation.org/kubecon-cloudnativecon-europe/co-located-events/submission-reviewer-guidelines-co-located-events/
- https://events.linuxfoundation.org/archive/2020/kubecon-cloudnativecon-north-america/program/scoring-guidelines/
- https://events.linuxfoundation.org/archive/2025/kubecon-cloudnativecon-north-america/features-add-ons/submission-reviewer-guidelines-maintainer-summit/

## 5. Speaker bio

- Current LF pages state no limit. Sessionize privacy note: "speaker name, company, job title, biography and photo will appear on the public schedule."
- Historic limits: 500 characters for every speaker and panelist (2023 co-located PDF); 800 characters, third person (2022 EU template).
- Guidance: third person; include previous speaking experience (NA 2020 form).
- Sessionize also stores a short tagline and a photo per profile; the bio is entered once and reused across events.
- Recommendation for the tool: target 500 characters or fewer, third person.

Sources: the 2023 PDF, 2022 template, and Sessionize event pages listed above.

## 6. Submission platform

- Sessionize for all CNCF CFPs since NA 2023 (previously SMApply).
- Event slugs seen: `kubecon-cloudnativecon-europe-2027`, `kubecon-cloudnativecon-north-america-2026`, `kubecon-cloudnativecon-india-2026`, `kubecon-cloudnativecon-japan-2026`, `kubecon-cloudnativecon-openinfra-pytorch-2026`, `cncf-hosted-co-located-events-europe-2027`, `cncf-hosted-co-located-events-north-america-2026`, `maintainer-summit-eu-2027`, `kccncjapan-projectlt-maintainer-track`, `project-benefits-kubecon-eu-2026`.
- Form structure is not public (login wall, verified with curl). Sessionize supports custom questions with conditional logic.
- Login via Google, Microsoft, Facebook, X, or a classic account. Progress saves automatically. Co-speakers are invited by email. Post-submit editing depends on organizer settings; historically submissions were final with title and abstract editable after acceptance.
- Contacts: cfp@cncf.io (main CFP), cncfcolocatedevents@linuxfoundation.org (co-located), ProjectsAtKubeCon@linuxfoundation.org (project benefits), support@sessionize.com (account issues).

Sources:

- https://sessionize.com/kubecon-cloudnativecon-europe-2027/
- https://sessionize.com/kubecon-cloudnativecon-north-america-2026/
- https://sessionize.com/kubecon-cloudnativecon-india-2026/
- https://cncf.io/blog/2023/04/26/introducing-sessionize-a-new-cfp-platform-for-cncf-events
- https://sessionize.com/playbook/case-study-linux-foundation

## 7. Date patterns

| Event | Event dates | CFP open | CFP close | Notify | Schedule |
|---|---|---|---|---|---|
| EU 2027 Barcelona | 15-18 Mar 2027 | 10 Aug 2026 | 11 Oct 2026 23:59 CEST | 7 Dec 2026 | 9 Dec 2026 |
| EU 2027 co-located | 15 Mar 2027 | 2 Sep 2026 | 18 Oct 2026 | 14 Dec 2026 | 16 Dec 2026 |
| EU 2027 Maintainer Summit | 14 Mar 2027 | 23 Sep 2026 | 1 Dec 2026 | 5 Jan 2027 | 6 Jan 2027 |
| NA 2026 Salt Lake City | 9-12 Nov 2026 | 6 Apr 2026 | 31 May 2026 23:59 MT | 3 Aug 2026 | 5 Aug 2026 |
| NA 2026 co-located | 9 Nov 2026 | | 21 Jun 2026 | 17 Aug 2026 | 19 Aug 2026 |
| China 2026 Shanghai | 7-9 Sep 2026 | | 3 May 2026 23:59 CST | 15 Jun 2026 | 17 Jun 2026 |
| Japan 2026 Yokohama | 29-30 Jul 2026 | 20 Jan 2026 | 29 Mar 2026 23:59 JST | 11 May 2026 | 13 May 2026 |
| India 2026 Mumbai | 18-19 Jun 2026 | 2 Dec 2025 | 1 Feb 2026 23:59 IST | 9 Mar 2026 | 11 Mar 2026 |
| EU 2026 Amsterdam | 23-26 Mar 2026 | | 12 Oct 2025 | 8 Dec 2025 | 10 Dec 2025 |
| NA 2025 Atlanta | 10-13 Nov 2025 | | 27 May 2025 | 28 Jul 2025 | 30 Jul 2025 |

Pattern: CFP opens about 7-8 months before the event, runs about 8 weeks, closes about 5 months before the event on a Sunday at 11:59 PM in the host city's time zone. Notifications arrive about 3 months before the event, always on a Monday; the schedule is published the Wednesday after. Co-located CFPs close about a week after the main CFP and notify about a week later.

Sources: the CFP and Sessionize pages listed in sections 1 and 6, plus https://sessionize.com/kubecon-cloudnativecon-japan-2026/.

## 8. Differences between editions and co-located events

- The main CFP field set is identical across EU, NA, Japan, China, and India (same LF page template). Differences: track names (section 3), tutorial length (EU 80 vs 75 elsewhere), poster sessions only at EU and NA, China uses "Suggested Topics" and is co-hosted with OpenInfra Summit and PyTorch Conference, NA 2025 allowed 2 submissions versus 3 elsewhere.
- No language field was found for Japan, China, or India. Descriptions are expected in English. Unverified whether Chinese-language submissions are accepted for China.
- Co-located events: shorter formats (25/35/10 minutes), one event plus an event-specific topic, panels need three organizations instead of "more than one," 10-minute lightning talks instead of 5, the speaker benefit is an All-Access ticket covering KubeCon, and a different contact address.
- Project benefits CFP: different eligibility, no documented "benefits to the ecosystem" emphasis, Project Lightning Talks give no complimentary pass.

Sources: sections 1 and 2.

## 9. What makes a KubeCon abstract get accepted

### 9a. Acceptance rates

| Event | Submissions | Accepted | Rate | Notes |
|---|---|---|---|---|
| EU 2025 London | 2,947 | | 8% | 36% of accepted talks from end users; 26% gender-minority speakers |
| NA 2024 | 1,937 (2,110 speakers, 961 companies) | 218 (plus 90 SIG slots), 348 speakers | 11% | End users 46% of submissions and accepted talks, 27% of accepted speakers |
| EU 2024 | 2,541 (2,746 speakers, 1,228 companies) | 223 (plus 90 SIG slots), 377 speakers | 9% | End users 45% of accepted talks |
| EU 2023 | 1,761 | 186 | 11% | |
| NA 2022 | 1,526 | 166 | 11% | |
| NA 2021 | 976 | 139 | 14% | |
| Copenhagen 2018 | 1,087 | 157 sessions + 16 lightning | 17.6% | |

CNCF's stated averages: Europe about 1,800 submissions at 10%, North America about 1,800 at 12%, China about 500 at 17%. Trend: 17% (2018) to 11% (2022-2024) to 8% (EU 2025). Roughly 90 to 97 slots per event are reserved for the Maintainer Track and are not in the open CFP pool. No NA 2025 or 2026 "Inside the Numbers" post was found.

Sources:

- https://www.cncf.io/blog/2025/05/09/tea-peaches-kubecon-cloudnativecon-london-recap-atlanta-sneak-peek/
- https://www.cncf.io/blog/2024/08/19/inside-the-numbers-the-kubecon-cloudnativecon-selection-process-for-north-america-2024/
- https://www.cncf.io/blog/2024/01/30/inside-the-numbers-the-kubecon-cloudnativecon-selection-process-for-europe-2024/
- https://www.cncf.io/blog/2023/02/08/inside-the-numbers-the-kubecon-cloudnativecon-selection-process-for-europe-2023/
- https://www.cncf.io/blog/2022/08/03/inside-the-numbers-the-kubecon-cloudnativecon-selection-process-for-north-america-2022/
- https://www.cncf.io/blog/2018/05/29/get-your-kubecon-talk-accepted/

### 9b. How reviewers score (public rubric)

Each proposal gets at least five program committee reviewers in its track. Four criteria are scored 1-5 stars (half stars allowed), plus a "Not a Product Pitch" rating.

| Criterion | 1 star | 3 stars | 4 stars | 5 stars |
|---|---|---|---|---|
| Content | "Unclear, incoherent, incomplete or AI-generated" | Clear and structured, but predictable or lacking depth | Well written, coherent, strong fit for the format and level | Highly engaging, polished, high-impact audience takeaways |
| Originality | "Generic, copied, a product pitch, or AI slop" | Interesting ideas but presented before or lacking clear updates | Clear new angle or innovative approach | Bold, highly creative, novel insights for KubeCon |
| Relevance | Not relevant to CNCF/KubeCon, little audience value | Relevant but narrow or niche | Strongly aligned with conference goals, broad audience value | "Timely, significant cloud native challenges with wide community impact" |
| Speaker(s) | Examples of unengaging presentations or weak slides | Personal experience with the topic and engaging content creation (blogs, docs), even if not talks | Topic expertise and clear examples of presented content | Recognized leader with recorded examples of engaging talks |
| Not a Product Pitch | Clear focus on proprietary software without wider ecosystem value | Reviewer uncertain, with comment | | Non-proprietary software, no signs of vendor pitching |

Speaker 2 stars = "No examples of presentation experience, and unclear depth with the topic." The Additional Resources field (a talk recording) therefore drives this score directly.

Selection-stage balancing (2021 CNCF post, possibly stale): at least 8% women or non-binary speakers per shortlist, 30-40% first-time KubeCon speakers, no company over-represented, a good end-user share, and beginner/advanced balance. The 2023 co-located best-practices page used "RO SQI" (Relevance, Originality, Soundness, Quality of Presentation, Importance) and told reviewers to give "only 2 or 3 fives."

Sources:

- https://events.linuxfoundation.org/kubecon-cloudnativecon-europe/program/submission-reviewer-guidelines/
- https://events.linuxfoundation.org/archive/2020/kubecon-cloudnativecon-north-america/program/scoring-guidelines/
- https://events.linuxfoundation.org/archive/2023/kubecon-cloudnativecon-europe/co-located-events/cfp-guidelines-best-practices-cncf-hosted-co-located-events/
- https://www.cncf.io/blog/2021/03/08/a-look-inside-the-kubecon-cloudnativecon-schedule-selection-process/

### 9c. Is "benefits to the ecosystem" weighted?

Yes, explicitly. The LF CFP pages state the abstract is "one of two primary factors the Program Committee will use to measure the strength and relevance of the presentation" and, about Benefits: "as with the abstract, the relevance of your presentation is just as important as the content and that second determining factor in acceptance." It maps to the Relevance criterion and partly to Originality. It is reviewer-only, so it is the place to say why now, who benefits (personas), what is new versus prior talks, your credentials, and what data or case study you will show.

Rey Lejano (CNCF Ambassador, KubeCon reviewer): "Do not underestimate the power of the Benefits to the Ecosystem section"; it "is not a copy pasta of your proposal"; "describe how your talk will add to the community knowledge base, tools, processes, people"; "note different personas who you may be targeting in your talk and the value provided to each."

Sources:

- https://events.linuxfoundation.org/kubecon-cloudnativecon-north-america/program/cfp/
- https://gist.github.com/reylejano/b78b054e3d6943c330d6852501d4d7df

### 9d. Concrete guidance from CNCF, co-chairs, and reviewers

Official LF CFP page guidance (current):

- Description must emphasize "the problem, your contribution, and its relevance" with "technical details without losing sight of the big picture." Full sentences, third person, error-free, concise. Title case; attendees pick talks by title.
- Sample submission on the page: "OCI, CRI, ??: Making Sense of the Container Runtime Landscape in Kubernetes." Its Benefits text opens with a recurring community pain point (confusing runtime choices) and lists concrete things covered (gVisor, Firecracker, Kata Containers, RuntimeClass).
- "Preparing to submit" questions: What are you hoping to get from your presentation? What do you expect the audience to gain? How will your presentation help better the ecosystem?
- Dawn Foster's talk is linked from every CFP page as the official how-to: https://youtu.be/2I5fYBLCfUA (content not fetched).

Co-chairs 2025 (Abby Bangser, Joseph Sandoval, Faseela K):

- "We saw many great proposals submitted under the wrong tracks."
- "Think about the full story." "You don't need to have a perfect ending; honesty and lessons learned are powerful."
- They look for talks that "highlight the hard parts, what's been learned, what's still unknown."
- The co-chairs do not decide alone; a large program committee scores proposals. Submit to both KubeCon and a co-located Day-0 event.

CNCF (Dan Kohn, 2018; marked out of date but echoed on current pages):

- "We want talk selection to be meritocratic and vendor-neutral."
- Focus on open source project work. Pick a unique topic "less likely to be submitted by multiple people" because only one of many similar proposals gets picked.
- Accepted talks "have clear, compelling titles and descriptions."
- Link a recorded talk, blog posts, or repos to establish credentials, especially for a first talk.
- Mark end-user case studies and consider an end-user co-presenter.
- Submit your best idea, at most two.

OpenSSF podcast, Feb 2026, with KubeCon NA keynote speakers Stacey Potter and Adolfo Garcia Veytia:

- "Be clear, be specific with your value proposition in the first two sentences."
- Name the audience level. Tailor each submission to the conference. Ask what makes it unique.
- A product pitch is "the first big no-no." Reviewers prefer typos over AI-flattened text. Write the draft yourself and use AI only for editing.

Community reviewers and speakers:

- Alex Ellis (CNCF Ambassador): reviewers handle 100-200 proposals, so "Your first sentence is where you can make an impact." Use short paragraphs. Original content is safer because reviewers search for repeats. End-user production stories "bring balance to pure tech talks." Wrong track is an instant rejection.
- Kaslin Fields: state takeaways explicitly ("Attendees will walk away learning X, Y, Z"). Supplemental materials are optional "but do not skip it."
- Kubernetes blog 2018: the committee may change your audience level based on the description.

Sources:

- https://events.linuxfoundation.org/kubecon-cloudnativecon-north-america/program/cfp/
- https://www.cncf.io/blog/2025/05/09/tea-peaches-kubecon-cloudnativecon-london-recap-atlanta-sneak-peek/
- https://www.cncf.io/blog/2018/05/29/get-your-kubecon-talk-accepted/
- https://openssf.org/podcast/2026/02/03/whats-in-the-soss-podcast-50-s3e2-demystifying-the-cfp-process-with-kubecon-north-america-keynote-speakers/
- https://blog.alexellis.io/how-to-speak-at-kubecon/
- https://kaslin.rocks/apply-to-speak-kubecon-cfp/
- https://kubernetes.io/blog/2018/10/18/tips-for-your-first-kubecon-presentation-part-1/
- https://gist.github.com/reylejano/b78b054e3d6943c330d6852501d4d7df

### 9e. Common rejection reasons

1. Vendor or product pitch, or closed-source focus: "almost always rejected" (LF pages); 1-star Originality and Not-a-Product-Pitch (rubric); "reviewers can smell it from a mile away" (Lejano).
2. Vague, generic, bullet-list-only, or AI-generated text: 1-star Content and Originality explicitly name "AI slop"; repeat offenders can be banned; "Don't submit a bulleted list of topics without any explanation" (Lejano).
3. Duplicate of a talk given at any LF event in the past year, or one of many similar submissions on a hot topic: rule on every CFP page; Originality capped at 3 stars for "presented before or lacking clear updates."
4. Missing or unclear takeaways and audience value: Relevance and Content criteria; co-chairs want "the hard parts" and lessons learned.
5. Wrong track or mislabeled audience level: co-chairs cite it as a top issue in 2025; reviewers are instructed to flag it.
6. No evidence of speaking ability: Speaker criterion gives 2 stars for "no examples of presentation experience."
7. Rule violations that remove the proposal from review: more than 3 submissions, 3+ speakers all identifying as men, panelists from a single company, panelists not named at submission.
8. Program balance rather than quality: same speaker or company already selected, too many talks in one niche, diversity targets. CNCF repeats "If your talk was not accepted, it doesn't mean it wasn't great," and rejected submitters may request reviewer feedback through cfp@cncf.io.

## Unverified items and flags

1. Current character limits for title, description, benefits, and bio are not stated on any official 2025 or 2026 page. Historic numbers: 75 / 1,300 / 1,000 / 500-800. Recommend the tool uses these as soft targets and warns the user.
2. Exact current Sessionize question labels and option lists (audience level values, end-user yes/no, prior-KubeCon-speaker yes/no, diversity questions) are inferred from 2022 and 2023 forms. The live EU 2027 form is open until 11 Oct 2026 and would confirm everything with a Sessionize login.
3. Whether a free-text "Audience" field still exists (only in the tracypholmes gist).
4. Whether KubeCon Sessionize submissions are editable after submission.
5. The 2021 diversity percentages (8% women or non-binary, 30-40% first-time speakers) have not been restated in newer posts.
6. No official CFP office hours recordings or a 2025/2026 CNCF "how to write a CFP" blog post were found. Dawn Foster's YouTube talk is the only officially linked tutorial and was not fetched.
7. No NA 2025 or 2026 acceptance numbers were found.
8. Keynotes: no open CFP type found; they appear to be invited or promoted from accepted talks.
9. Language policy for China, Japan, and India editions is not stated.
10. The EU 2026 co-located cap (2 per event, 10 total) was not confirmed on the EU 2027 co-located page.
