# Quickstart results: XDG configuration and neutral store default

Date: 2026-11-27. Run from the worktree on branch `002-xdg-config-store`.

## Automated

| Command | Result |
|---------|--------|
| `make test` | 330 passed |
| `make test-hook` | OK: hook emits `<cfp-context>` |
| `make lint-dashes` | OK: no em-dash or en-dash characters |

## Script-level scenarios (scratch HOME)

Each scenario ran with `env -i HOME=<scratch>/<scenario> PATH=...` and `python3 -I`, with scratch folders under the session scratchpad. The real `~/.config/cc-cfp` and `~/.local/share/cc-cfp` were not touched.

| # | Scenario | Outcome |
|---|----------|---------|
| 1 | Neutral default (SC-001): `config show` | PASS: `store` = `<scratch>/.local/share/cc-cfp/store`, `store_source` = `default` |
| 2 | XDG variables: `config init --speaker-name T --seed-dir cfp/knowledge-base/profiles` with `XDG_DATA_HOME` and `XDG_CONFIG_HOME` | PASS: wrote `<scratch>/cfg/cc-cfp/config.json`, created `<scratch>/data/cc-cfp/store` |
| 3 | Legacy config (SC-002) with `XDG_CONFIG_HOME` set | PASS: `store_source` = `config`, `config_file` = `<scratch>/.config/cc-cfp/config.json` |
| 4 | Relative variable `CFP_STORE=talks` | PASS: exit 1, `CFP_STORE must be an absolute path, got 'talks'` |
| 5 | Personal profiles (SC-004): `acme-summit` and a `kubecon` variant with `seed_version: 2099-01-01` | PASS: seeded `kubecon` (user variant) and `acme-summit`, exactly one clash warning |
| 6 | Hook agreement (SC-003) for scenarios 1 to 4 | PASS: `<store>` equals `config show` `store` for 1 to 3; for 4, empty `<store>` and `<store-error>` equal to the CLI error |

## Docs search (SC-005)

8. `rg -n -i "obsidian" README.md docs/guide/content specs/001-cfp-plugin/{spec.md,plan.md,research.md,contracts} cfp/skills/init/SKILL.md`: PASS. Every statement that the store defaults to an Obsidian vault is either rewritten (README, guide, init skill) or carries a "Superseded by feature 002" note (feature 001 `spec.md` Input and FR-001, `plan.md` Summary, Storage, and research summary, `contracts/commands.md` init Asks, `contracts/store-files.md` config example). The remaining matches say that Obsidian can render or edit the store, which stays true (FR-017).

## Interactive scenario for the user (not run here)

7. In a Claude Code session with a scratch HOME (`HOME=<scratch> claude`, plugin installed from this checkout):
   - Create two vault folders, for example `<scratch>/Obsidian/private` and `<scratch>/Obsidian/work`.
   - Create a `kubecon` variant: copy `cfp/knowledge-base/profiles/kubecon` to `<scratch>/.local/share/cc-cfp/profiles/kubecon` and raise its `seed_version`.
   - Run `/cfp:init` and check:
     - the default store is offered first as the absolute path `<scratch>/.local/share/cc-cfp/store`;
     - `<scratch>/Obsidian/private/Talks` and `<scratch>/Obsidian/work/Talks` are offered as further choices, plus free text;
     - the `kubecon` clash warning appears exactly once, although both `config init` (Step 5) and `profile seed-status` (Step 6) return it;
     - the final report names the config file and the personal profiles folder (`user_profiles_dir`).
