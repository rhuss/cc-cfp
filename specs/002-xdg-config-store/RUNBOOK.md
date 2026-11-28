---
runbook_version: 1
feature: 002-xdg-config-store
status: drafted
mode: light
steps_total: 9
step_results: pending,pending,pending,pending,pending,pending,pending,pending,pending
drafted_at: c7e7aec
drafted_fingerprint: ee87b75d16a4f78a2fe125fac9b9af1ad7d8b1a2d876cbd0206889c1840bebb9
tested_at:
tested_fingerprint:
updated: 2026-11-27
---

# Try it: XDG configuration and neutral store default

<!-- runbook-status -->
> **Status:** drafted · 0 of 9 steps · Mode: light · Drafted at c7e7aec · 2026-11-27
<!-- /runbook-status -->

## What you're testing

cfp no longer defaults to an Obsidian vault. Its config follows XDG (`CFP_CONFIG_DIR`, `$XDG_CONFIG_HOME/cc-cfp`, `~/.config/cc-cfp`), the store falls back to `<data folder>/store` (`~/.local/share/cc-cfp/store`), and personal conference profiles in `<data folder>/profiles` are seeded next to the shipped ones, overriding a shipped profile of the same name with a warning.

The journey runs from the root of this checkout with throwaway HOME folders under `specs/002-xdg-config-store/.walkthrough/`, so your real `~/.config/cc-cfp` and `~/.local/share/cc-cfp` are never touched. Order: prepare scratch homes, see the neutral default, initialize a store, relocate the config, check the legacy fallback, compare the session hook with the CLI, add personal profiles, try `/cfp:init` interactively, and search the docs.

## Test environment

No fixtures. Every step uses `env -i HOME=...` with a scratch folder created in Step 1 and the system `python3`.

## Steps

### Step 1 of 9: Prepare scratch home folders

**Why this step:** every later step needs an empty HOME so the result depends only on the variables the step sets.

**Needs:** a shell in the root of this checkout.

**Run:**

```
rm -rf specs/002-xdg-config-store/.walkthrough/h && mkdir -p specs/002-xdg-config-store/.walkthrough/h/a specs/002-xdg-config-store/.walkthrough/h/b specs/002-xdg-config-store/.walkthrough/h/c specs/002-xdg-config-store/.walkthrough/h/d && ls specs/002-xdg-config-store/.walkthrough/h
```

**What you should see:** the four folder names `a b c d`.

**If you see something else:** a permission error means the checkout is read-only; run from a writable clone.

**Result:**

### Step 2 of 9: The neutral default store (US1)

**Why this step:** with nothing configured, cfp must resolve the store to the XDG data folder instead of failing or pointing at Obsidian (FR-005, SC-001).

**Needs:** Step 1.

**Run:**

```
env -i HOME="$PWD/specs/002-xdg-config-store/.walkthrough/h/a" PATH="$PATH" python3 -I cfp/scripts/cfp_store.py config show
```

**What you should see:** JSON with `"ok": true`, `"store"` ending in `.walkthrough/h/a/.local/share/cc-cfp/store`, `"store_source": "default"`, `"exists": false`, `"config_file": null`, `"config_write_path"` ending in `h/a/.config/cc-cfp/config.json`, and `"user_profiles_dir"` ending in `h/a/.local/share/cc-cfp/profiles`.

**If you see something else:** `store_source` other than `default` means a variable leaked in (check that the command starts with `env -i`).

**Result:**

### Step 3 of 9: Initialize a store at the default (US1)

**Why this step:** init must create the default store with its parents and save it in the XDG config file, without creating the personal profiles folder (FR-008, FR-011).

**Needs:** Step 2.

**Run:**

```
env -i HOME="$PWD/specs/002-xdg-config-store/.walkthrough/h/a" PATH="$PATH" python3 -I cfp/scripts/cfp_store.py config init --speaker-name "Try It" --seed-dir cfp/knowledge-base/profiles && cat specs/002-xdg-config-store/.walkthrough/h/a/.config/cc-cfp/config.json && ls specs/002-xdg-config-store/.walkthrough/h/a/.local/share/cc-cfp
```

**What you should see:** init JSON with `"ok": true`, `kubecon` in `seeded_profiles`, `"warnings": []`; then `config.json` with `"store"` pointing at `.../h/a/.local/share/cc-cfp/store`; then only `store` listed (no `profiles` folder).

**If you see something else:** a `profiles` entry in the listing means init created the personal folder, which FR-011 forbids.

**Result:**

### Step 4 of 9: Relocate the config with CFP_CONFIG_DIR (US2)

**Why this step:** the config file must follow `CFP_CONFIG_DIR` and nothing may be written to `~/.config/cc-cfp` (FR-001).

**Needs:** Step 1.

**Run:**

```
env -i HOME="$PWD/specs/002-xdg-config-store/.walkthrough/h/b" CFP_CONFIG_DIR="$PWD/specs/002-xdg-config-store/.walkthrough/h/b/myconf" PATH="$PATH" python3 -I cfp/scripts/cfp_store.py config init --speaker-name "Try It" --seed-dir cfp/knowledge-base/profiles && ls specs/002-xdg-config-store/.walkthrough/h/b/myconf && ls -a specs/002-xdg-config-store/.walkthrough/h/b
```

**What you should see:** `"ok": true` with `config_write_path` ending in `h/b/myconf/config.json`; `myconf` holds `config.json`; the HOME listing shows `.local` and `myconf` but no `.config`.

**If you see something else:** a `.config` folder in the HOME listing means the write ignored `CFP_CONFIG_DIR`.

**Result:**

### Step 5 of 9: Legacy config still found under a new XDG_CONFIG_HOME (US2)

**Why this step:** users from feature 001 have `~/.config/cc-cfp/config.json`; it must still be read when `XDG_CONFIG_HOME` points elsewhere and holds no cfp config (FR-003, SC-002).

**Needs:** Step 1.

**Run:**

```
mkdir -p specs/002-xdg-config-store/.walkthrough/h/c/.config/cc-cfp && printf '{"store": "%s"}\n' "$PWD/specs/002-xdg-config-store/.walkthrough/h/c/oldstore" > specs/002-xdg-config-store/.walkthrough/h/c/.config/cc-cfp/config.json && env -i HOME="$PWD/specs/002-xdg-config-store/.walkthrough/h/c" XDG_CONFIG_HOME="$PWD/specs/002-xdg-config-store/.walkthrough/h/c/xdg" PATH="$PATH" python3 -I cfp/scripts/cfp_store.py config show
```

**What you should see:** `"store"` ending in `h/c/oldstore`, `"store_source": "config"`, `"config_file"` ending in `h/c/.config/cc-cfp/config.json` (the legacy file), and `"config_write_path"` ending in `h/c/xdg/cc-cfp/config.json`.

**If you see something else:** `store_source: default` means the legacy fallback did not run.

**Result:**

### Step 6 of 9: Session hook agrees with the CLI, and reports bad variables (US2)

**Why this step:** the `<cfp-context>` hook and the scripts must resolve the same store (FR-004), and a relative `CFP_STORE` must become a `<store-error>` instead of a fake path (FR-002a).

**Needs:** Step 5.

**Run:**

```
echo '{"prompt":"/cfp:status"}' | env -i HOME="$PWD/specs/002-xdg-config-store/.walkthrough/h/c" XDG_CONFIG_HOME="$PWD/specs/002-xdg-config-store/.walkthrough/h/c/xdg" PATH="$PATH" python3 -I cfp/hooks/scripts/context-hook.py; echo; echo '{"prompt":"/cfp:status"}' | env -i HOME="$PWD/specs/002-xdg-config-store/.walkthrough/h/c" CFP_STORE=talks PATH="$PATH" python3 -I cfp/hooks/scripts/context-hook.py; echo " exit=$?"
```

**What you should see:** first JSON: `additionalContext` contains `<store>` with the same `.../h/c/oldstore` path as Step 5. Second JSON: `<store></store>`, `<store-initialized>false</store-initialized>`, and `<store-error>CFP_STORE must be an absolute path, got 'talks'</store-error>`, followed by `exit=0`.

**If you see something else:** a different store path in the first output means the hook and CLI disagree (FR-004 broken); a non-zero exit means the hook would disturb the session.

**Result:**

### Step 7 of 9: Personal profiles and a clash with a shipped one (US3)

**Why this step:** profiles in `<data folder>/profiles` must be seeded like shipped ones, and a same-named variant must win with exactly one warning (FR-010, FR-012, SC-004).

**Needs:** Step 1.

**Run:**

```
mkdir -p specs/002-xdg-config-store/.walkthrough/h/d/.local/share/cc-cfp/profiles && cp -R cfp/knowledge-base/profiles/kubecon specs/002-xdg-config-store/.walkthrough/h/d/.local/share/cc-cfp/profiles/acme-summit && cp -R cfp/knowledge-base/profiles/kubecon specs/002-xdg-config-store/.walkthrough/h/d/.local/share/cc-cfp/profiles/kubecon && perl -pi -e 's/^seed_version:.*/seed_version: "2099-01-01"/' specs/002-xdg-config-store/.walkthrough/h/d/.local/share/cc-cfp/profiles/kubecon/profile.md && env -i HOME="$PWD/specs/002-xdg-config-store/.walkthrough/h/d" PATH="$PATH" python3 -I cfp/scripts/cfp_store.py config init --speaker-name "Try It" --seed-dir cfp/knowledge-base/profiles && env -i HOME="$PWD/specs/002-xdg-config-store/.walkthrough/h/d" PATH="$PATH" python3 -I cfp/scripts/cfp_store.py profile seed-status --seed-dir cfp/knowledge-base/profiles
```

**What you should see:** init JSON with `acme-summit` and `kubecon` in `seeded_profiles` and one `warnings` entry starting with `profile 'kubecon': using` and naming the personal folder and the shipped folder. Then `seed-status` with a `kubecon` entry whose `source` is `user`, `state` `current`, `seed_version` `2099-01-01`, an `acme-summit` entry with `source` `user`, and the same single clash warning.

**If you see something else:** `kubecon` with `source: plugin` means the override did not apply; two warnings in one result means duplicates.

**Result:**

### Step 8 of 9: Interactive /cfp:init with vaults and a clash (US1, US3)

**Why this step:** the init skill must offer the XDG default first, list vault folders only as extra choices, show the clash once, and name the personal profiles folder (FR-006, FR-007, FR-012).

**Needs:** Step 7, and the plugin installed from this checkout under the scratch HOME of this step (sub-step 2), because `make install` registers it in the `~/.claude` of the HOME it runs under.

**Do:**

1. In a terminal, create two vault folders: `mkdir -p specs/002-xdg-config-store/.walkthrough/h/d/Obsidian/private specs/002-xdg-config-store/.walkthrough/h/d/Obsidian/work`.
2. Install the plugin under that HOME: `HOME="$PWD/specs/002-xdg-config-store/.walkthrough/h/d" make install`.
3. Start Claude Code with that HOME and without path overrides from your shell: `env -u CFP_STORE -u CFP_CONFIG_DIR -u CFP_DATA_DIR -u XDG_CONFIG_HOME -u XDG_DATA_HOME HOME="$PWD/specs/002-xdg-config-store/.walkthrough/h/d" claude` (log in if asked).
4. Run `/cfp:init`, choose "re-run setup" or follow the prompts, and accept defaults.

**What you should see:** the store question offers the absolute `.../h/d/.local/share/cc-cfp/store` first (recommended), then `.../Obsidian/private/Talks` and `.../Obsidian/work/Talks`, plus free text. The `kubecon` clash warning appears exactly once in the run. The final report names the config file and the personal profiles folder.

**If you see something else:** an Obsidian path as the first choice means Step 1 of the init skill still uses the old default; a repeated warning means de-duplication is missing.

**Result:**

### Step 9 of 9: Documentation no longer names Obsidian as the default (US4)

**Why this step:** README, guide, and feature 001 artifacts must describe the new default (FR-016, FR-017, SC-005).

**Needs:** nothing.

**Run:**

```
rg -n -i "obsidian" README.md docs/guide/content cfp/skills/init/SKILL.md specs/001-cfp-plugin/spec.md specs/001-cfp-plugin/plan.md specs/001-cfp-plugin/research.md specs/001-cfp-plugin/contracts
```

**What you should see:** every remaining match either says Obsidian can render or edit the store, or offers vault folders as a choice, or carries "Superseded by feature 002". No line claims the store defaults to an Obsidian vault.

**If you see something else:** a line like "default `~/Obsidian/<vault>/Talks`" without a superseded note is a missed doc.

**Result:**

## Coverage

- US1 (neutral default): Steps 2, 3, 8.
- US2 (XDG config, hook parity): Steps 4, 5, 6.
- US3 (personal profiles): Steps 7, 8.
- US4 (docs): Step 9.

All four user stories are covered. The full 16-combination matrix of SC-003 is covered by `cfp/scripts/test/test_hook.py`, not by hand.

## Results
