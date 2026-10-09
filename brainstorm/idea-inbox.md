# Idea Inbox

Ideas captured from code reviews for future brainstorming.

### repeat-rule-note-semantics

- **Source**: deep-review
- **Date**: 2026-10-09
- **Reference**: 001-cfp-plugin
- **Summary**: The one-year repeat rule downgrades to a warning whenever the previously-presented field is non-empty, and the draft skill always fills it, so for KubeCon it can never disqualify a finished proposal.

> FR-030 says "when a previously-presented note exists"; whether the note explains significant differences is a different test. A confirmation question or a minimum-length heuristic needs a spec clarification first.

### review-rounds-name-collision

- **Source**: deep-review
- **Date**: 2026-10-09
- **Reference**: 001-cfp-plugin
- **Summary**: review_rounds is the integer round limit in config.md and the list of recorded rounds on a proposal.

> Same key, two types, both read in the same draft step. A future contract revision could rename the config key to max_review_rounds with a fallback.

### skill-name-prefix-convention

- **Source**: deep-review
- **Date**: 2026-10-09
- **Reference**: 001-cfp-plugin
- **Summary**: Skill frontmatter uses name cfp:<dir> while the agent uses the bare name; validation passes today.

> If the loader ever enforces the documented character set for skill names, all seven skills stop loading at once.

### pasteview-kind-unused

- **Source**: deep-review
- **Date**: 2026-10-09
- **Reference**: 001-cfp-plugin
- **Summary**: The JSON paste view emits a kind per field that nothing reads.

> Either drop it or use it to skip the character count line for choice and boolean fields.

### family-profile-approval-reset

- **Source**: deep-review
- **Date**: 2026-10-09
- **Reference**: 001-cfp-plugin
- **Summary**: Rewriting a family profile keeps approved true from the existing file, unlike event overrides which reset to false.

> FR-010 asks before changing the family profile, but only skill prose enforces it; mirroring the event behavior in profile write would back it in the script.

### hook-interpreter-guard

- **Source**: deep-review
- **Date**: 2026-10-09
- **Reference**: 001-cfp-plugin
- **Summary**: The UserPromptSubmit hook launches python3 on every prompt; a missing interpreter shows a shell error in every project.

> Wrapping the command in command -v python3 and a trailing or true keeps sessions that never use cfp silent. A 5 second timeout is already set.

### seed-profile-refresh

- **Source**: deep-review
- **Date**: 2026-10-09
- **Reference**: 001-cfp-plugin
- **Summary**: A seed profile already in the store is never refreshed; seed_version is written but never compared.

> Plugin updates that correct limits or add event files reach only new stores. init could copy missing event and example files and report seed updates.

### non-latin-slugs

- **Source**: deep-review
- **Date**: 2026-10-09
- **Reference**: 001-cfp-plugin
- **Summary**: Titles in non-Latin scripts slugify to item, item-2, and so on.

> The draft skill could propose an ASCII id when the slug degenerates, or fall back to a short hash of the title.

### preflight-rerun-drops-manual-findings

- **Source**: deep-review
- **Date**: 2026-10-09
- **Reference**: 001-cfp-plugin
- **Summary**: A pre-flight re-run replaces the stored findings and drops manual ones such as the audience-level warning; no test pins this.

> The skills re-add the finding after each run, so behavior is consistent, but a test should state the intended semantics.

### autouse-home-isolation

- **Source**: deep-review
- **Date**: 2026-10-09
- **Reference**: 001-cfp-plugin
- **Summary**: HOME isolation in the test suite is an opt-in fixture.

> A future test calling init_store without the fixture would write the real user config; an autouse fixture makes the isolation structural.

### post-pass-draft-edits

- **Source**: deep-review
- **Date**: 2026-10-09
- **Reference**: 001-cfp-plugin
- **Summary**: A draft with a passing review can be edited and then set ready after a clean pre-flight without a new review; intentional for the voice pass and shortening.

> If a stricter model is wanted, mark-voice-pass could become the only sanctioned post-pass edit path and other edits would mark the review stale.
