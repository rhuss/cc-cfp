# cc-cfp: conference proposals and speaker bios for Claude Code

`cfp` is a Claude Code plugin that drafts conference talk proposals (CFP submissions) and speaker bios interactively, using reusable conference profiles. It ships with a KubeCon + CloudNativeCon profile built from the public CFP pages, the reviewer rubric, and the hard rules, so the first proposal can start right after installation.

The workflow is talk-centric. A talk holds the conference-independent story (problem, contribution, takeaways, personas, what is new, prior outings). A proposal renders that talk for one conference edition, field by field, with a simulated program committee review, a voice pass through the prose plugin, a pre-flight rule check, and a paste view with character counts. Nothing is ever submitted on your behalf: you paste the texts into the conference site yourself.

## Install

Install the plugin from the [cc-rhuss-marketplace](https://github.com/rhuss/cc-rhuss-marketplace):

```text
/plugin marketplace add rhuss/cc-rhuss-marketplace
/plugin install cfp@cc-rhuss-marketplace
```

To pick up a new release later, run `/plugin marketplace update cc-rhuss-marketplace` and then `/cfp:init` (see [First run](#first-run)).

Requirements: Claude Code with plugin support and Python 3.10 or newer on `PATH`. The scripts use only the standard library and run with `python3 -I`, so no virtual environment is needed at runtime.

Optional: the `prose` plugin from [cc-prose](https://github.com/rhuss/cc-prose) (`prose:humanizer` skill) for the voice pass. Without it the voice pass is skipped with a notice.

## First run

```text
/cfp:init
```

Asks for the store path, your name, company, a voice profile, and the maximum number of committee review rounds. The proposed store path is `~/.local/share/cc-cfp/store` (more precisely `<data folder>/store`, see [Configuration](#configuration)), shown as a full path. When `~/Obsidian/<vault>` folders exist, up to three `~/Obsidian/<vault>/Talks` folders are offered as further choices, and you can type any other path. Init creates the store, saves its path in the config file (`~/.config/cc-cfp/config.json` by default), and copies the shipped KubeCon profile and your personal profiles into the store as approved profiles.

Run `/cfp:init` again after a plugin update. The store keeps its own copy of the shipped profile, and when the shipped one is newer, `/cfp:init` shows the differences and offers to update the copy. The update replaces whole files, keeps the approval of the profile and its events, and never touches events or examples you added yourself.

The store is resolved in this order: `--store <path>` on a CLI call, the `CFP_STORE` environment variable, the `store` entry of the config file, then the default `<data folder>/store`. Set `CFP_STORE` to point a session at a second store without rewriting the config file; the context hook honours it too.

## Configuration

cfp uses two folders outside the store. Both follow the [XDG Base Directory](https://specifications.freedesktop.org/basedir-spec/latest/) layout and can be moved with an environment variable.

| Folder | Location, first match wins | Holds |
|---|---|---|
| Config folder | `CFP_CONFIG_DIR`, then `$XDG_CONFIG_HOME/cc-cfp`, then `~/.config/cc-cfp` | `config.json` with the store path |
| Data folder | `CFP_DATA_DIR`, then `$XDG_DATA_HOME/cc-cfp`, then `~/.local/share/cc-cfp` | `profiles/` (your personal profiles) and the default `store/` |

Rules for the variables:

- `XDG_CONFIG_HOME` and `XDG_DATA_HOME` are ignored when they are empty or not absolute.
- `CFP_CONFIG_DIR`, `CFP_DATA_DIR`, and `CFP_STORE` count as unset when empty. A leading `~` is expanded; a value that is still relative is an error that names the variable.
- When `CFP_CONFIG_DIR` is not set and the config folder holds no `config.json`, cfp reads `~/.config/cc-cfp/config.json` (the location of earlier versions). Writes always go to the config folder.
- `python3 -I cfp/scripts/cfp_store.py config show` reports the config file in use, the data folder, the personal profiles folder, the store, and where the store came from (`argument`, `environment`, `config`, or `default`).

### Personal conference profiles

Put conference profiles that the plugin does not ship into `<data folder>/profiles/<id>/`, in the same format as the shipped `cfp/knowledge-base/profiles/kubecon/` (a folder with `profile.md`, optional `events/` and `examples/`). `/cfp:init` copies them into a new store next to the shipped ones, and its update check compares the store copy with your profile. cfp never creates this folder.

- `seed_version` in `profile.md` is an ISO date (`YYYY-MM-DD`). Raise it when you change the profile, and `/cfp:init` offers the update.
- A profile without `seed_version` is copied once and never offered updates.
- A personal profile with the name of a shipped one replaces it, and cfp warns about it. To have your variant offered over an existing store copy of the shipped profile, give it a later `seed_version` than the shipped one.

## Commands

| Command | What it does |
|---|---|
| `/cfp:init [--store <path>]` | First-use setup and seed profile copy; on later runs, the update of a shipped profile that a newer plugin version brought |
| `/cfp:draft [--profile <id>] [--event <id>] [--talk <id>] [--proposal <id>] [--from <path or URL>]` | Interactive drafting from an idea, existing material, a stored talk, or an old proposal: story interview, title and abstract angles, every form field, committee review loop, voice pass, pre-flight, paste view |
| `/cfp:bio [new \| list \| edit <name> \| delete <name> \| resource add \| resource list \| resource delete <id>]` | Bio variations (third person, with character counts) and speaker resources (recordings, repositories, blog posts, prior sessions) |
| `/cfp:profile [new <name or URL> \| refresh <id> [--event <id>] [--screenshots <paths>] \| show <id> \| list]` | Research a conference's public CFP pages and form screenshots into a profile, refresh an edition's event override, inspect profiles and deadlines |
| `/cfp:check <proposal-id>` | Standalone pre-flight: hard rules, the profile's custom rules, audience level check, character counts, and whether the proposal can become ready |
| `cfp:committee-review --proposal <id>` (skill) | One simulated program committee round on a stored proposal; `/cfp:draft` runs it in its review loop |
| `/cfp:status [list [--status <s>] \| set <id> <status> [--date <d>] \| reopen <id> [--event <id>]]` | Lifecycle: draft, ready, submitted, accepted, rejected, withdrawn, presented; reopen a rejected proposal for another event |

## Store layout

Everything is plain markdown with YAML front matter. You can edit it in any editor or open the store as an Obsidian vault.

```text
<store>/
  config.md                      speaker name, company, voice profile, review rounds, default profile
  profiles/<family>/profile.md   session types, form fields with limits, rubric, rules, rejection reasons
  profiles/<family>/events/*.md  per-edition overrides: dates, tracks, submission limit, session type variations
  profiles/<family>/examples/*.md calibration examples (accepted texts, official samples)
  talks/<talk>.md                the conference-independent story
  proposals/<event>--<talk>.md   one talk rendered for one event, with review rounds and pre-flight results
  bios/<name>.md                 bio variations
  resources/<id>.md              speaker resources
```

Files can be edited by hand as long as the front matter stays valid. A file with broken front matter is reported with its path and the problem, and the rest of the store keeps working.

The front matter of `config.md` has these keys: `speaker_name`, `speaker_company`, `voice_profile`, `review_rounds` (default 3), and `default_profile`. `default_profile` is the profile `/cfp:draft` offers first; `/cfp:init` sets it to the first profile in the store when it is empty. One more key is optional and `/cfp:init` does not ask for it: `speaker_gender`. Add it by hand when a profile has a rule about speaker line-ups in which every speaker is a man (KubeCon has one for sessions with three or more speakers). Without it, the pre-flight check warns that it could not confirm the rule.

## Confirming the KubeCon limits

The shipped profile carries the limits confirmed on the KubeCon EU 2027 Sessionize form (abstract 1000, bio 500, marked `screenshot`) and the historic title limit of 75 (marked `unverified`, the paste view labels it as approximate). The reviewer-only relevance field is `value_to_community` and CNCF plus other open source projects share one field, `cncf_oss_projects`. The live form sits behind a login, so to re-confirm limits for a new edition, open the form, take screenshots of each page, and run:

```text
/cfp:profile refresh kubecon --event kubecon-eu-2027 --screenshots ~/Desktop/form-1.png,~/Desktop/form-2.png
```

Limits confirmed by a screenshot become `limit_status: screenshot` with the file name as source.

## Voice pass

After a passing committee review, the title, abstract, reviewer-only relevance field, and bio snapshot are run through `prose:humanizer` from the [cc-prose](https://github.com/rhuss/cc-prose) plugin with the voice profile from `config.md`. Voice profiles are the named YAML files under `~/.claude/style/voices/`. cc-prose also reads one project voice from `.style/voice.yaml` in the directory a session runs in, and applies it before the named profile. The pass changes only the proposal's bio snapshot, never the stored bio variation, and the character counts are rechecked afterwards.

## Development

To work on the plugin itself, install it from your checkout instead of the marketplace. `make install` adds the repository as the local `cc-cfp-marketplace` and installs `cfp@cc-cfp-marketplace` from it; run it again after each change. Uninstall the marketplace copy first (`/plugin uninstall cfp@cc-rhuss-marketplace`) so the two do not load side by side, and use `make uninstall` to remove the development copy again.

```bash
git clone https://github.com/rhuss/cc-cfp.git
cd cc-cfp
make install       # install the plugin from this checkout (development only)
uv venv ~/.venvs/cc-cfp
uv pip install --python ~/.venvs/cc-cfp/bin/python -r cfp/requirements-dev.txt
make validate      # claude plugin validate on both manifests
make test          # pytest over cfp/scripts/test
make test-hook     # the context hook emits <cfp-context>
make lint-dashes   # no em-dash or en-dash characters in cfp/ or README.md
```

The deterministic parts (front matter, counts, rule evaluation, status transitions, paste view) live in `cfp/scripts/cfplib/` behind the single CLI `cfp/scripts/cfp_store.py`, which prints one JSON object per call. The interactive flows live in `cfp/skills/`, the reviewer persona in `cfp/agents/committee-reviewer.md`, and the seed profile and guidance in `cfp/knowledge-base/`.

## License

Apache-2.0
