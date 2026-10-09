---
name: cfp:init
description: This skill should be used when the user runs "/cfp:init", asks to "set up the cfp store", "initialize cfp", "configure the cfp plugin", or when another cfp skill finds the store uninitialized. First-use setup: store path, speaker name, voice profile, review rounds, and seed profile copy.
argument-hint: "[--store <path>]"
allowed-tools: ["Bash", "Read", "AskUserQuestion", "Glob"]
---

# cfp:init

Set up the store the first time (or re-point an existing one). Follow Step 0 and the shared rules in `skills/_shared/preamble.md` under `PLUGIN_ROOT`, except that this skill never offers to run itself.

## Step 1: Store path

If `$ARGUMENTS` contains `--store <path>`, use it without asking.

Otherwise pick a default:

- Use Glob on `~/Obsidian/*` (directories). If exactly one vault exists, default to `~/Obsidian/<vault>/Talks`. If several exist, offer each `~/Obsidian/<vault>/Talks` as a choice plus "Other".
- If `~/Obsidian` does not exist, default to `~/cfp-store`.

If `<store-initialized>` is already `true`, show the current store path from `<store>` and ask whether to keep it, re-run setup on it (values will be updated, data is kept), or point to a different path.

Ask (AskUserQuestion): "Where should the store live?" with the default and "Other" (free text). Expand `~`.

## Step 2: Speaker name and company

Ask for the speaker name (required, used in third-person bios and drafts). Then ask for the company or affiliation (optional, used in bios and by any conference rule that compares speaker affiliations). Do not ask for anything a specific conference's rules need beyond this; the draft flow collects co-speaker details when a session type requires them, and the pre-flight check names the config key to set when a rule cannot be evaluated.

## Step 3: Voice profile

Look for prose plugin voice profiles with Glob: `~/.claude/style/voices/*.yaml` and `.style/voices/*.yaml` in the current project. If any exist, offer the file stems as choices plus "None (humanize only)". If none exist, say that no voice profiles were found, the voice pass will run the humanizer without a voice, and continue with an empty value. The user can also type a name that does not exist yet.

## Step 4: Review rounds

Ask how many committee review rounds to run at most before the loop stops (default 3, accept 1 to 10).

## Step 5: Initialize

Run:

```bash
python3 -I "$PLUGIN_ROOT/scripts/cfp_store.py" config init \
  --store "<store path>" --speaker-name "<name>" \
  --speaker-company "<company>" --voice-profile "<voice or empty>" \
  --review-rounds <n> --seed-dir "$PLUGIN_ROOT/knowledge-base/profiles"
```

Omit `--speaker-company` and `--voice-profile` when empty. The command creates `profiles/`, `talks/`, `proposals/`, `bios/`, `resources/`, writes `<store>/config.md`, writes `~/.config/cc-cfp/config.json`, and copies every seed profile that is not already in the store (seeded profiles are marked approved so drafting works immediately).

On `"ok": false`, show the error and ask whether to try a different path.

## Step 6: Report

Print a short summary:

- Store path
- Seeded profiles (from `seeded_profiles`), or "no new profiles seeded (already present)"
- Speaker, company, voice profile, review rounds
- Next command: `/cfp:draft` to start a proposal, `/cfp:bio new` to add a bio first, `/cfp:profile list` to see the conferences and their deadlines

Mention that every store file is plain markdown with front matter and can be edited in Obsidian.
