# Generating title and abstract angles

A talk story has five sections (Problem, Contribution, Takeaways, What is new, Story notes) plus a persona list and a project list. The same story can be pitched from several directions. Derive three distinct angles before writing any abstract, then let the user choose. The goal is not three rewordings of one idea but three different hooks that a reviewer would experience as different talks.

## Angle 1: problem-first

Open with the pain, promise the fix.

- When it fits: the Problem section describes something the personas feel today, and the Contribution solves or clearly reduces it. Best for operational, security, and performance topics where the audience already knows it hurts.
- How to open: first sentence names who hurts and what hurts, in concrete terms from the Problem section. Second sentence says what the talk changes about that. Example shape: "Platform teams that run agents on shared clusters discover that ... This session shows how ...".
- Risk to avoid: a generic pain everyone has already heard ("Kubernetes is complex"). If the problem sentence could open a hundred other talks, pull a specific detail from Story notes (a number, a failure, a named component) into it.

## Angle 2: story-driven

What we built or broke, and the honest lessons.

- When it fits: Story notes contain a real sequence of events, ideally in production, with decisions that turned out right or wrong. Co-chairs explicitly want "the hard parts, what's been learned, what's still unknown." End-user production stories balance the program and are favored in selection.
- How to open: first sentence states the situation and the stakes ("In 2025 the team moved 400 services to ..."). Second sentence states the outcome honestly, including what did not work. The abstract then walks through the turning points and ends with the lessons as explicit takeaways.
- Risk to avoid: a hero narrative where everything worked. Reviewers trust honesty more than success. You do not need a perfect ending; the story needs a clear lesson, not a clean victory. Also avoid company-specific detail nobody else can reuse.

## Angle 3: contrarian or myth-busting

Challenge a common belief, back it with evidence.

- When it fits: What is new contains a finding that contradicts current folklore, or the Contribution shows that a widely recommended practice fails under real conditions. Scores well on Originality ("clear new angle") when the evidence is real.
- How to open: first sentence states the belief as the community holds it. Second sentence says the talk shows it is wrong, incomplete, or outdated, and names the evidence (benchmarks, incident data, a measured migration).
- Risk to avoid: contrarian for its own sake. Without data from Story notes or What is new, the angle reads as a hot take and reviewers will mark Content down. If the evidence is thin, fall back to angle 1 or 2.

## What makes a title specific

Attendees pick talks by title, and reviewers see the title before anything else.

- Title case, under about 75 characters (the historic KubeCon limit).
- Names the concrete technology, project, or outcome. "Mixing gVisor and Kata Containers in One Cluster with RuntimeClass" beats "Container Runtimes Explained".
- Avoids generic words: "journey", "deep dive", "unleashing", "demystifying", "the power of", "best practices", "101" (unless the track is Novice).
- Follows the LF Inclusive Language Initiative (no master/slave, blacklist/whitelist, and similar terms).
- A hook helps: a question, a number, a surprising pairing, or a short colon-separated setup. Keep the hook honest; the subtitle must still say what the talk covers.
- Test: cover the abstract and read only the title. Can a reader say which persona the talk is for and what they will learn? If not, rewrite.

## The two-sentence value rule

The first two sentences of the abstract must carry the full value proposition: who it is for, what problem it addresses, and what the audience gets. Reviewers read 100 to 200 proposals each and form a judgment in the first lines. The abstract is also published verbatim on the schedule if accepted, so the opening is what attendees read when they decide whether to come. Everything after sentence two supports those claims; nothing after sentence two may introduce the main point for the first time.

## Abstract structure

Write the abstract in this order, in full sentences, in the third person (use the speaker name or "the speakers", never "I" or "we"):

1. Problem: who hurts, what hurts, why it matters now (one short paragraph).
2. Contribution: what the speakers built, measured, broke, or learned, with named technologies and projects.
3. Relevance: why this matters beyond the speakers' own setup, and what level of audience it targets.
4. Explicit takeaways: a closing sentence that starts with "Attendees will leave with ..." or "Attendees will learn ..." and lists two to four concrete outcomes.

Rules that apply to every abstract:

- No bullet lists. Reviewers reject "a bulleted list of topics without any explanation."
- Include the hard parts and lessons learned; a frictionless story reads as marketing.
- Technical detail without losing the big picture: name components and numbers, but keep each paragraph readable by someone outside the subfield.
- Fit the character limit from the profile (KubeCon: historically 1,300 characters, unverified). Leave headroom of about 50 characters for later edits.
- Spell-check, no vendor or product pitch, no closed-source focus.

## How to present candidates

Show two or three candidates in one message, never more than three at once. Each candidate has:

- A label: problem-first, story, or contrarian.
- A title (with its character count).
- An abstract draft (with its character count against the limit).
- A one-line note on the hook used and which talk story section it leans on.

Then ask the user to pick one or request another round. If the user wants another round, ask what to change (different hook, different persona emphasis, more or less story) before regenerating, and replace only the candidates they rejected.

## Worked mini example

Talk story (condensed):

- Problem: platform teams added coding agents to an internal developer platform and the agents created runaway namespaces and burned the CI budget.
- Contribution: admission policies with Kyverno plus Argo CD sync windows that cap agent actions; measured 70 percent fewer incidents over three months.
- Takeaways: a policy set to copy, a checklist for agent guardrails, what still breaks.

Candidates:

1. Problem-first: "Runaway Agents on the Platform: Guardrails with Kyverno and Argo CD" (68 chars). Hook: names the pain (runaway agents) and the fix in one line; leans on Problem and Contribution.
2. Story: "What Broke When We Let Agents Loose on Our Developer Platform" (62 chars). Hook: honest failure story with measured recovery; leans on Story notes and Takeaways.
3. Contrarian: "RBAC Is Not Enough: Why Agents Need Admission Policies, Not Roles" (65 chars). Hook: challenges the belief that RBAC covers agent safety, backed by the incident data; leans on What is new.
