---
name: cfp:bio
description: This skill should be used when the user runs "/cfp:bio", asks to "write a speaker bio", "create a bio variation", "list my bios", "edit my bio", "delete a bio", "add a speaker resource", "add a talk recording", "list my resources", or "remove a resource". Manages named third-person bio variations with character counts and the speaker resource list (recordings, repositories, blog posts, prior sessions, publications).
argument-hint: "[new | list | edit <name> | delete <name> | resource add | resource list | resource delete <id>]"
allowed-tools: ["Bash", "Read", "Write", "AskUserQuestion", "Skill"]
---

# cfp:bio

Maintain bio variations and speaker resources in the store. Follow Step 0 and the shared rules in `skills/_shared/preamble.md` under `PLUGIN_ROOT`.

## Subaction

Parse `$ARGUMENTS`:

| Arguments | Subaction |
|---|---|
| empty or `list` | List bios and resources |
| `new` | Create a bio variation |
| `edit <name>` | Edit a bio variation |
| `delete <name>` | Delete a bio variation |
| `resource add` | Add a speaker resource |
| `resource list` | List resources |
| `resource delete <id>` | Delete a resource |

Anything else: show this table and ask which subaction to run.

Bios are stored by `bio write --name <n> --emphasis <s> --target-length <n> --text-file <file>`. Bio texts never go on the command line; write them to a file in the session scratchpad first.

## `list`

Run `bio list` and `resource list`. Render the bios as a table:

| Name | Emphasis | Chars | Target | Updated |
|---|---|---|---|---|

Show `chars/target_length` in the Chars column when a target exists. Below the table add one line per resource type with its count (for example "Resources: 2 recordings, 1 repository"), or "No resources yet. Add a recording with `/cfp:bio resource add`." when the list is empty.

Report `problems` from both calls once (path and error) and continue. When there are no bios, say so and point to `/cfp:bio new`.

## `new`

1. Run `config show` and take `speaker_name`, `speaker_company`, `voice_profile`, and `default_profile` from `config`.
2. Ask (AskUserQuestion) for the emphasis: offer `cloud-native`, `ai`, `general`, and `other` (free text).
3. Ask for the target length in characters. Take the suggestion from the default profile instead of from memory: when `default_profile` is set, run `profile show --profile <default_profile>` and read `profile.name`, `bio_on_form`, `bio_limit`, and `bio_limit_status`. With a bio limit, suggest it and say in one sentence which conference it belongs to and how sure it is: "confirmed on the form" for `screenshot`, "stated on the CFP page" for `page`, "unverified, the live form may differ" for `unverified`. When there is no default profile, the call fails, `bio_on_form` is false, or the profile has no bio limit, suggest 500 as a common length and say that it is not tied to a conference. Other profiles can have other limits; `/cfp:draft` shows every bio against the limit of the proposal's own profile. Accept any positive number.
4. Ask whether there is source material: `paste text` (the user pastes it in the next message), `file` (ask for the path, then Read it), `existing bio` (run `bio list`, offer the names, then `bio show --name <n>` and adapt it), or `none`.
5. Draft a bio in the third person using the speaker's name. Rules: name in the first sentence, current role and company when known, one or two concrete things the speaker has built or maintains, speaking or community activity when the material supports it, no superlatives, no lists, no em-dash or en-dash. Aim for the target length minus a small margin so a later voice pass does not push it over.
6. Voice pass: if the `prose:humanizer` skill is available, invoke it via the Skill tool with the draft and the voice profile name (when set). Use the returned text. If the skill is not available, say "prose plugin not installed, skipping the voice pass" and keep the draft. If the skill returns usage text instead of a rewrite, keep the draft.
7. Print the complete draft verbatim in a fenced block in the message, followed by its count as `<chars>/<target> chars`. When over the target, say by how much. Never describe the bio instead of printing it; the user must be able to read every sentence before the next question.
8. Edit loop. Ask (AskUserQuestion): `save`, `change something` (the user describes the change, redraft, show again with the count), `regenerate` (new draft from the same inputs, show again), or `cancel`. Repeat until save or cancel.
9. Ask for a name. Propose a slug built from length and emphasis, for example `short-cloud-native` or `long-ai` (`short` when the target is at most 600 characters, `long` otherwise). The user can accept or type another slug (lowercase, digits, hyphens). If `bio list` already contains the name, ask whether to overwrite or pick another name.
10. Write the final text to `<scratchpad>/bio-<name>.txt` with the Write tool and run:

```bash
python3 -I "$PLUGIN_ROOT/scripts/cfp_store.py" bio write \
  --name "<name>" --emphasis "<emphasis>" --target-length <n> \
  --text-file "<scratchpad>/bio-<name>.txt"
```

`--name` is a slug and `--emphasis` one of the offered words; when the user typed a free-text emphasis under `other`, reduce it to a single lowercase word (letters and hyphens) before passing it.

11. Report the stored path and `chars` from the result as `<chars>/<target>`. Mention `/cfp:bio list` and that the bio can be picked during `/cfp:draft`.

## `edit <name>`

1. Run `bio show --name <name>`. On `"ok": false`, show the error, run `bio list`, and ask which bio to edit.
2. Show the current text with `<chars>/<target_length> chars`.
3. Ask what should change (free text; typical answers: shorten to N characters, add a project, change the emphasis, update the role).
4. Redraft with the change applied, keep everything else, run the voice pass as in `new` step 6, and show the result with its count against the target.
5. Edit loop as in `new` step 8.
6. On save, write the text to `<scratchpad>/bio-<name>.txt` and run `bio write --name "<name>" --text-file <file>`. Pass `--emphasis` and `--target-length` only when the user changed them; omitted values are kept.
7. Report the new `chars` against the target.

## `delete <name>`

Run `bio show --name <name>` to confirm it exists and show the first 100 characters. Ask (AskUserQuestion) "Delete bio `<name>`?" with `yes` and `no`. On yes run `bio delete --name "<name>"` and report `deleted`. Note that proposals keep their own bio snapshot, so deleting a variation does not change stored proposals.

## `resource add`

1. Ask the type (AskUserQuestion): `recording`, `repository`, `blog`, `session`, `publication`, `other`. Explain in one line that recordings count most for the Speaker criterion.
2. Ask the title.
3. Ask the link (URL).
4. Ask for the date (ISO `YYYY-MM-DD`, optional, press enter or answer "skip" to omit).
5. Ask for notes (optional, one line, for example the event or the talk the recording belongs to).
6. Write `<scratchpad>/resource.json` with the keys `type`, `title`, `link`, and `date` and `notes` only when given, then run:

```bash
python3 -I "$PLUGIN_ROOT/scripts/cfp_store.py" resource write --from-json "<scratchpad>/resource.json"
```

7. Report the `id` and path.
8. Run `resource list --type recording`. When `resources` is empty, recommend adding a recording: reviewers score the Speaker criterion higher when a talk recording is linked (FR-027), and `/cfp:draft` offers recordings first in the resources field. Ask whether to add one now; on yes repeat from step 2 with type `recording`.

## `resource list`

Run `resource list` (pass `--type <t>` when the user named a type). Render:

| Id | Type | Title | Link | Date |
|---|---|---|---|---|

Order recordings first, then the remaining types. Report `problems` once. When empty, point to `/cfp:bio resource add`.

## `resource delete <id>`

Run `resource list`, find the id, and show its type, title, and link. When the id is unknown, show the table and ask which to delete. Ask "Delete resource `<id>`?" with `yes` and `no`. On yes run `resource delete --id "<id>"` and report `deleted`. Proposals that reference the id keep the reference; mention this when the user asks.
