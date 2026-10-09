---
id: lf-sample-container-runtime
profile: kubecon
event: KubeCon + CloudNativeCon (Linux Foundation CFP page sample)
year: 2023
origin: official-sample
proposal:
added: 2026-10-09
---

## Title

OCI, CRI, ??: Making Sense of the Container Runtime Landscape in Kubernetes

## Abstract

Kubernetes operators face a confusing set of container runtime choices. Docker, containerd, and CRI-O all claim to run containers, the dockershim has been removed from the kubelet, and new sandboxed runtimes promise stronger isolation. Few teams can explain what actually changes when they switch runtimes, or which runtime a given workload needs.

This session untangles the landscape from the ground up. It explains what the Open Container Initiative (OCI) image and runtime specifications define, what the Container Runtime Interface (CRI) adds on the Kubernetes side, and where high-level runtimes such as containerd and CRI-O sit relative to low-level runtimes such as runc. It then shows how RuntimeClass lets a single cluster run several runtimes side by side, including gVisor, Firecracker, and Kata Containers, and routes each pod to the right one.

Attendees will leave with a clear mental model of the runtime stack, a decision guide for choosing between containerd, CRI-O, and sandboxed runtimes, and a working RuntimeClass setup they can apply to their own clusters.

## Benefits

Operators keep asking the same question in Slack channels, SIG meetings, and support tickets: which container runtime should we choose, and does it even matter? The dockershim removal made this pain acute, and the arrival of sandboxed runtimes made the answer harder rather than easier. Cluster operators gain a decision guide they can apply the same week. Platform engineers gain a RuntimeClass pattern for mixing runtimes without running separate clusters. Security teams gain a concrete picture of what gVisor, Firecracker, and Kata Containers isolate and what each costs in startup time and compatibility. The session is vendor neutral, covers only OCI and CNCF projects, and ends with a live RuntimeClass demonstration rather than slides alone.

## Why it worked

Note: the abstract and benefits texts above are a reconstruction summarized from the research document (brainstorm/research/kubecon-cfp-research.md, section 9d). They are not the verbatim Linux Foundation sample text. The title is the one shown on the LF CFP page.

- The title is specific and has a hook. "OCI, CRI, ??" signals confusion in three tokens, then the subtitle names the exact technology (container runtimes) and the exact context (Kubernetes). A reader scanning a schedule knows what they get.
- The first sentence states the pain. Reviewers handle 100 to 200 proposals, and the opening line says who hurts (operators) and why (confusing runtime choices) before any technology is explained.
- The benefits text does not restate the abstract. It opens with the recurring community pain point as reviewers experience it (the same question in Slack and SIG meetings), then says why now (dockershim removal, sandboxed runtimes). None of its sentences could be pasted into the abstract.
- Concrete named technologies replace generic claims. gVisor, Firecracker, Kata Containers, and RuntimeClass are listed by name, which tells reviewers the depth is real and lets them judge originality.
- Clear personas with distinct gains. Cluster operators, platform engineers, and security teams each get a one-line statement of what they walk away with, which is exactly what the Relevance criterion scores.
- Explicit takeaways close the abstract. "Attendees will leave with ..." lists three outcomes, so the Content criterion ("high-impact audience takeaways") has something to score.
