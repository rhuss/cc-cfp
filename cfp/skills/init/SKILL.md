---
name: cfp:init
description: This skill should be used when the user runs "/cfp:init", asks to "set up the cfp store", "initialize cfp", "configure the cfp plugin", "update the shipped profile", "update the seed profile", or when another cfp skill finds the store uninitialized. First-use setup (store path, speaker name, voice profile, review rounds, seed profile copy) and, on an existing store, the update of a shipped profile that a newer plugin version brought.
argument-hint: "[--store <path>]"
allowed-tools: ["Bash", "Read", "AskUserQuestion", "Glob"]
---

# cfp:init

Set up the store the first time, re-point an existing one, or bring its copy of a shipped profile up to date. Follow Step 0 and the shared rules in `skills/_shared/preamble.md` under `PLUGIN_ROOT`, except that this skill never offers to run itself.

## Step 1: Store path

If `$ARGUMENTS` contains `--store <path>`, use it without asking.

If `<store-initialized>` is already `true`, show the current store path from `<store>` and ask (AskUserQuestion) one of:

- `keep it as it is`: no setting changes. Skip Steps 2 to 5 and continue with Step 6, which checks the shipped profiles.
- `re-run setup on it`: Steps 2 to 5 update the values; all data is kept.
- `use a different path`: ask for the path, then continue with Step 2.

Otherwise pick a default:

- Run `python3 -I "$PLUGIN_ROOT/scripts/cfp_store.py" config show` and take `store` from the result. It is an absolute path: `CFP_STORE` when set, else the `store` entry of the config file, else the neutral default `<data folder>/store` (for example `~/.local/share/cc-cfp/store`). On `"ok": false`, show the error (it names the environment variable to fix) and stop.
- Use Glob on `~/Obsidian/*` (directories). For up to three vaults, sorted by name, add `~/Obsidian/<vault>/Talks` as further choices. Never make a vault the default; further vaults can be typed into the free-text option.

Ask (AskUserQuestion): "Where should the store live?" with the default first, marked as recommended and shown as the full absolute path, then the vault choices, then "Other" (free text). Expand `~`.

## Step 2: Speaker name and company

Ask for the speaker name (required, used in third-person bios and drafts). Then ask for the company or affiliation (optional, used in bios and by any conference rule that compares speaker affiliations). Do not ask for anything a specific conference's rules need beyond this; the draft flow collects co-speaker details when a session type requires them, and the pre-flight check names the config key to set when a rule cannot be evaluated.

## Step 3: Voice profile

Look for the named voice profiles of the prose plugin with Glob: `~/.claude/style/voices/*.yaml`, and `~/.claude/prose/voices/*.yaml` for profiles from older cc-prose versions. If any exist, offer the file stems (each name once) as choices plus "None (humanize only)". If none exist, say that no voice profiles were found, the voice pass will run the humanizer without a named voice, and continue with an empty value. The user can also type a name that does not exist yet.

cc-prose also knows one project voice: the file `.style/voice.yaml` (older: `.prose/voice.yaml`) in the directory a session runs in. It has no name, so it is not a choice here. When Glob finds one in the current directory, tell the user that cc-prose applies it before the named profile in every session started in this directory.

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

Omit `--speaker-company` and `--voice-profile` when empty. The command creates the store folder (with missing parents), `profiles/`, `talks/`, `proposals/`, `bios/`, `resources/`, writes `<store>/config.md`, saves the store path in the config file named by `config_write_path` in the result, and copies every seed profile that is not already in the store (seeded profiles are marked approved so drafting works immediately). Seeds come from the shipped profiles and from the user's personal profiles in `user_profiles_dir`; the command finds that folder itself, and a missing folder is fine. It never overwrites a profile that is already there; Step 6 handles those.

Keep the `warnings` of the result for this run and show each one once. Two kinds can appear:

- `CFP_STORE is set to ... and overrides the saved store ...`: tell the user to remove or change the variable if the chosen path should win.
- `profile '<name>': using <user folder> instead of the shipped <plugin folder>`: a personal profile replaces the shipped one of the same name. Step 6 reports the same clash again; show it only once per run (de-duplicate by profile name).

On `"ok": false`, show the error and ask whether to try a different path.

## Step 6: Seed profile updates

The store keeps its own copy of every seed profile, shipped or personal. After a plugin update the shipped profile can be newer than that copy, and the user can raise the `seed_version` of a personal profile. Check it on every run, also when Step 1 kept the store as it is:

```bash
python3 -I "$PLUGIN_ROOT/scripts/cfp_store.py" profile seed-status \
  --store "<store path>" --seed-dir "$PLUGIN_ROOT/knowledge-base/profiles"
```

The result has `seeds` and `warnings`. Show each entry of `warnings` that Step 5 did not show already in this run (de-duplicate by profile name), so every clash appears exactly once.

`seeds` has one entry per seed profile with `profile`, `state`, `store_version`, `seed_version`, `files`, `source` (`plugin` for a shipped profile, `user` for a personal one), and `seed_dir` (the folder it was read from). Act on `state`:

- `current`, `missing`, `local`: nothing to do and nothing to say. (`missing` is copied by Step 5; `local` means the store profile has no `seed_version`, so it was researched or written by hand, or seeded from a personal profile without `seed_version`, and is never replaced.)
- `newer` with `source: plugin`: say in one line that the store's `<profile>` profile comes from a newer plugin version than the installed one.
- `newer` with `source: user`: say in one line that the store copy's `seed_version` is higher than your profile's, so there is nothing to update.
- `unreadable`: show the `error` once.
- `outdated`: offer the update below, one profile at a time.

For an outdated profile:

1. Say which seed is newer than the copy in the store, with both versions (`store_version` to `seed_version`): "the shipped `<profile>` profile" for `source: plugin`, "your personal `<profile>` profile in `<seed_dir>`" for `source: user`.
2. For every entry in `files` with the state `changed`, print its path and then its `diff` in full in a fenced `diff` block. Explain once how to read it: lines starting with `-` are in the store now and would be replaced, lines starting with `+` come with the seed file (labeled `shipped/` or `user/`). Then list the files with the state `missing` (shipped files the store does not have). Files with the state `same` need nothing.
3. Ask (AskUserQuestion) what to do:
   - `update everything shown`: offer it only when a file other than `profile.md` is changed or missing.
   - `update the profile only`: `profile.md` is replaced, the other files stay as they are.
   - `skip`: nothing changes.
4. For the first two answers run (with `--all` for `update everything shown`, without it for the profile only):

```bash
python3 -I "$PLUGIN_ROOT/scripts/cfp_store.py" profile seed-update \
  --store "<store path>" --profile <profile> \
  --seed-dir "$PLUGIN_ROOT/knowledge-base/profiles" [--all]
```

   When the user wants some of the files only, pass `--files <path,path>` instead of `--all`, with the paths as `seed-status` printed them.
5. Report `updated`, `added`, and `skipped` from the result. Then run `profile validate --store "<store path>" --profile <profile>` and show `problems` when there are any.

What the update does and does not do, to tell the user before they choose:

- It replaces whole files. Hand edits in a replaced file are lost, which is why the diff comes first.
- The approval of the profile and of every replaced event stays as it was.
- Files that only the store has (events the user added, examples of accepted proposals) are never touched.
- After `update the profile only`, the store profile is current and the skipped files are not offered again. Their seed copies stay readable under `seed_dir`.
- After `skip`, the store copy stays as it is and the next `/cfp:init` run offers the update again.

## Step 7: Report

Print a short summary:

- Store path (absolute)
- Config file (`config_write_path` from Step 5, or `config_write_path` from `config show` when Step 1 kept the store)
- Personal profiles folder (`user_profiles_dir` from Step 5 or from `config show`): put personal conference profiles here
- Seeded profiles (from `seeded_profiles` of Step 5), or "no new profiles seeded (already present)"
- Seed profile updates applied or skipped in Step 6, with the versions and the source (shipped or personal)
- Speaker, company, voice profile, review rounds
- Next command: `/cfp:draft` to start a proposal, `/cfp:bio new` to add a bio first, `/cfp:profile list` to see the conferences and their deadlines

Mention that every store file is plain markdown with front matter and can be edited in any editor or opened as an Obsidian vault.
