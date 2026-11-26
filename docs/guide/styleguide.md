# cc-cfp style guide

Project terms and rules that every page follows, on top of the cc-prose voice profiles. Page implementers and reviewers read this file. Keep one rule per bullet.

## Terms

- "cfp" is the plugin name (lowercase, also in sentence-initial position written as `cfp` in monospace); "cc-cfp" is the repository and the guide title.
- "CFP" (uppercase) means a conference call for proposals.
- "talk" means the conference-independent story of a session; "proposal" means that talk rendered for one conference edition. Never use them interchangeably.
- "profile" means a conference profile (fields, limits, rubric, rules); "event" means one edition's override of a profile.
- "store" means the cfp data directory configured by `/cfp:init`.
- "committee review" means the simulated program committee review, never a real one.
- "voice pass" means the cc-prose humanizer step in `/cfp:draft`.
- "pre-flight" (with hyphen) means the rule check run by `/cfp:check` and by `/cfp:draft`.
- "paste view" means the final per-field output with character counts.
- Limit statuses are written in monospace as stored: `screenshot`, `unverified`.
- Product names are spelled exactly: Claude Code, cc-prose, KubeCon + CloudNativeCon, Sessionize, RainFocus, Red Hat Summit, Obsidian.
- Persona name: "User".
- Commands are written with their slash and namespace: `/cfp:draft`, `/cfp:init`.

## Rules

- No em dash or en dash characters.
- AsciiDoc pages: one sentence per line.
- Versions and commits come from the baseline attributes, never typed.
- Task pages: a short paragraph on why, then numbered steps, then a `Check:` line with the expected result.
- cfp never submits anything; pages never suggest it does.
- Example talks and proposals use fictional content, never the author's real talks or proposals.
