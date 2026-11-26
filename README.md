# cc-cfp: conference proposals and speaker bios for Claude Code

`cfp` is a Claude Code plugin that drafts conference talk proposals (CFP submissions) and speaker bios interactively, using reusable conference profiles. It ships with a KubeCon + CloudNativeCon profile built from the public CFP pages, the reviewer rubric, and the hard rules, so the first proposal can start right after installation.

The workflow is talk-centric. A talk holds the conference-independent story (problem, contribution, takeaways, personas, what is new, prior outings). A proposal renders that talk for one conference edition, field by field, with a simulated program committee review, a voice pass through the prose plugin, a pre-flight rule check, and a paste view with character counts. Nothing is ever submitted on your behalf: you paste the texts into the conference site yourself.

## Install

```bash
git clone https://github.com/rhuss/cc-cfp.git
cd cc-cfp
make install          # adds the local marketplace and installs cfp@cc-cfp-marketplace
```

Requirements: Claude Code with plugin support and Python 3.10 or newer on `PATH`. The scripts use only the standard library and run with `python3 -I`, so no virtual environment is needed at runtime.

Optional: the `prose` plugin from [cc-prose](https://github.com/rhuss/cc-prose) (`prose:humanizer` skill) for the voice pass. Without it the voice pass is skipped with a notice.

## First run

```text
/cfp:init
```

Asks for the store path (default `~/Obsidian/<vault>/Talks` when an Obsidian vault exists, else `~/cfp-store`), your name, company, a voice profile, and the maximum number of committee review rounds. It creates the store, writes `~/.config/cc-cfp/config.json` with the store path, and copies the shipped KubeCon profile into the store as an approved profile.

The store is resolved in this order: `--store <path>` on a CLI call, the `CFP_STORE` environment variable, then `~/.config/cc-cfp/config.json`. Set `CFP_STORE` to point a session at a second store without rewriting the config file; the context hook honours it too.

## Commands

| Command | What it does |
|---|---|
| `/cfp:init [--store <path>]` | First-use setup and seed profile copy |
| `/cfp:draft [--profile <id>] [--event <id>] [--talk <id>] [--proposal <id>] [--from <path or URL>]` | Interactive drafting from an idea, existing material, a stored talk, or an old proposal: story interview, title and abstract angles, every form field, committee review loop, voice pass, pre-flight, paste view |
| `/cfp:bio [new \| list \| edit <name> \| delete <name> \| resource add \| resource list \| resource delete <id>]` | Bio variations (third person, with character counts) and speaker resources (recordings, repositories, blog posts, prior sessions) |
| `/cfp:profile [new <name or URL> \| refresh <id> [--event <id>] [--screenshots <paths>] \| show <id> \| list]` | Research a conference's public CFP pages and form screenshots into a profile, refresh an edition's event override, inspect profiles and deadlines |
| `/cfp:check <proposal-id>` | Standalone pre-flight: hard rules, audience level check, character counts, and whether the proposal can become ready |
| `cfp:committee-review --proposal <id>` (skill) | One simulated program committee round on a stored proposal; `/cfp:draft` runs it in its review loop |
| `/cfp:status [list [--status <s>] \| set <id> <status> [--date <d>] \| reopen <id> [--event <id>]]` | Lifecycle: draft, ready, submitted, accepted, rejected, withdrawn, presented; reopen a rejected proposal for another event |

## Store layout

Everything is plain markdown with YAML front matter and renders in Obsidian.

```text
<store>/
  config.md                      speaker name, company, voice profile, review rounds
  profiles/<family>/profile.md   session types, form fields with limits, rubric, rules, rejection reasons
  profiles/<family>/events/*.md  per-edition overrides: dates, tracks, submission limit, session type variations
  profiles/<family>/examples/*.md calibration examples (accepted texts, official samples)
  talks/<talk>.md                the conference-independent story
  proposals/<event>--<talk>.md   one talk rendered for one event, with review rounds and pre-flight results
  bios/<name>.md                 bio variations
  resources/<id>.md              speaker resources
```

Files can be edited by hand as long as the front matter stays valid. A file with broken front matter is reported with its path and the problem, and the rest of the store keeps working.

## Confirming the KubeCon limits

The shipped profile carries the limits confirmed on the KubeCon EU 2027 Sessionize form (abstract 1000, bio 500, marked `screenshot`) and the historic title limit of 75 (marked `unverified`, the paste view labels it as approximate). The reviewer-only relevance field is `value_to_community` and CNCF plus other open source projects share one field, `cncf_oss_projects`. The live form sits behind a login, so to re-confirm limits for a new edition, open the form, take screenshots of each page, and run:

```text
/cfp:profile refresh kubecon --event kubecon-eu-2027 --screenshots ~/Desktop/form-1.png,~/Desktop/form-2.png
```

Limits confirmed by a screenshot become `limit_status: screenshot` with the file name as source.

## Voice pass

After a passing committee review, the title, abstract, reviewer-only relevance field, and bio snapshot are run through `prose:humanizer` from the [cc-prose](https://github.com/rhuss/cc-prose) plugin with the voice profile from `config.md`. Voice profiles are the YAML files under `~/.claude/style/voices/` (or `.style/voices/` in a project). The pass changes only the proposal's bio snapshot, never the stored bio variation, and the character counts are rechecked afterwards.

## Development

```bash
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
