# Writing a reviewer-only relevance field (Benefits to the Ecosystem)

## Why it matters

KubeCon's CFP pages call the abstract "one of two primary factors" in selection and say about the Benefits to the Ecosystem field: "the relevance of your presentation is just as important as the content and that second determining factor in acceptance." Other conferences have a similar reviewer-only field under names like "Notes to reviewers", "Why this talk", or "Audience benefit". Treat them all the same way.

Three facts shape how to write it:

- It is reviewer-only. Attendees never see it, so it does not need to sell the talk to the public. It needs to help a program committee member fill in a star rating and write the mandatory review comment.
- It maps to the Relevance criterion ("timely, significant cloud native challenges with wide community impact" at 5 stars) and partly to Originality ("clear new angle" versus "presented before or lacking clear updates").
- Rey Lejano, a long-time KubeCon reviewer, puts it this way: the field "is not a copy pasta of your proposal." Describe "how your talk will add to the community knowledge base, tools, processes, people" and "note different personas who you may be targeting in your talk and the value provided to each."

## Structure, in this order

Write short paragraphs or a single dense paragraph, not bullets, unless the profile says the form allows them.

1. Who benefits, by persona, with what each gains. Take the personas from the talk story and give each one a concrete outcome. "Platform engineers get a policy set they can apply this quarter; SREs get an incident checklist for agent workloads; security reviewers get a threat model for autonomous tooling." One sentence per persona is enough.
2. Why now. What changed in the ecosystem that makes this talk timely: a project milestone (a feature went GA, an API was removed, a project graduated), a shift in adoption, or a pain that is current in the community right now. Name the milestone and the version if you can.
3. What is new versus prior talks on the subject. Be explicit about the delta. If similar talks exist at earlier KubeCons or on YouTube, name them and say what this session adds (new data, a different scale, a failure they did not cover, a newer version). If the speakers gave an earlier version themselves, say so and list the changes; the one-year repeat rule requires it.
4. Evidence and credentials. Production use (how long, what scale), upstream contributions to the projects discussed, published data or blog posts, a case study with a named or described organization, and links to prior recordings. This is the cheapest way to raise the Speaker score, and reviewers use it to judge whether the depth is real.
5. What data or case study the session shows. State concretely what the audience will see: benchmark numbers, incident timelines, a live demo, an architecture that runs in production, configuration they can copy.

## The hard rule: do not restate the abstract

The abstract already told the reviewer what the talk is about. The benefits field answers a different question: why should this talk be on the schedule, and for whom. If the two texts overlap, the reviewer learns nothing new and the Relevance score stays at "relevant but narrow".

Test every sentence: if it could be pasted into the abstract unchanged, rewrite it or delete it. Sentences that pass the test talk about the community, the timing, the personas, the delta from prior work, or the speakers' evidence. Sentences that fail describe the talk's content.

## Good openings

- "Operators keep asking the same question in Slack and SIG meetings: which runtime should we pick, and does it matter? The dockershim removal made that question urgent."
- "Since the Gateway API reached GA, platform teams have been migrating off Ingress with almost no published production data on what breaks. This session supplies that data from a migration of 1,200 routes."
- "Three groups leave with something different: SREs get an incident checklist, platform engineers get a Kyverno policy set, and engineering managers get a cost model they can defend in a budget review."

Each opening names a current community pain, a timing trigger, or a persona split in its first sentence, and none of them describes the talk's content.

## Bad openings

- "This talk explains how RuntimeClass lets a cluster mix container runtimes such as gVisor and Kata Containers." Why it fails: it restates the abstract. The reviewer already read this.
- "This session is relevant to everyone in the cloud native community who works with Kubernetes." Why it fails: generic. No persona, no outcome, no reason why now. A reviewer cannot score it above "narrow or niche" because nothing specific is claimed.
- "Acme Platform solves these problems out of the box, and attendees will see how our customers benefit." Why it fails: vendor claim. It triggers the Not a Product Pitch rating and 1-star Originality, and the LF pages say such sessions are "almost always rejected".

## Worked example

Talk story (condensed): a platform team let coding agents act on an internal developer platform, agents created runaway namespaces and burned the CI budget, the team added Kyverno admission policies and Argo CD sync windows and measured 70 percent fewer incidents over three months. Personas: platform engineers, SREs, security reviewers.

Benefits text (about 820 characters, inside the historic 1,000 limit):

> Teams that added coding agents to their platforms in 2025 are now hitting the same incident pattern: agents with valid credentials doing valid things at a scale nobody budgeted for. Nothing in the current Kubernetes security talks covers this; they stop at RBAC and workload identity. Platform engineers leave with a Kyverno policy set they can apply this quarter. SREs get an incident checklist built from eleven real agent-caused outages. Security reviewers get a threat model that treats agents as a distinct principal class. The speakers run this setup in production for 40 teams, maintain the policies upstream in the Kyverno policy library, and will show the incident timeline and the three-month before and after numbers. The abstract was not presented before; a shorter internal version exists but no recording.

Why it passes the test: the first sentence is a community pain with a timing trigger (2025, agents), the second is the delta from prior talks, the next three give one gain per persona, then evidence (production scale, upstream contributions), then the data shown, then the repeat status. No sentence describes the talk's content in a way that belongs in the abstract.

## Adapting to other conferences

The structure above is KubeCon-shaped, but the same five parts fit any reviewer-only field. Adjust the emphasis:

- If the field is called "Notes to reviewers" or "Why should we pick this talk", lead with the delta and the evidence; personas can be one sentence.
- If the field is called "Audience benefit" or "What will attendees learn", lead with the personas and their gains; keep why now and evidence short.
- If the conference has no reviewer rubric published, still cover all five parts; reviewers without a rubric fall back on exactly these questions.
- If the profile marks the field as public rather than reviewer-only, drop the credentials paragraph (it reads as self-promotion on a schedule) and keep the personas and why now.

Check the field's `guidance` and `audience` values in the profile before drafting; they override these defaults.

## Checklist before saving the field

1. Every persona from the talk story appears with a concrete gain, and no persona is just "developers" or "everyone".
2. There is a "why now" sentence that names a milestone, version, or current community pain.
3. The delta from prior talks is explicit, with prior talks named if any exist (including the speakers' own).
4. At least one piece of evidence appears: production use, contributions, data, case study, or a prior recording link.
5. No sentence could be pasted into the abstract unchanged, and no sentence pitches a product or company.
6. The text fits the field's character limit from the profile (KubeCon: historically 1,000 characters, unverified), uses full sentences, and contains no bullet lists unless the profile says the form allows them.
