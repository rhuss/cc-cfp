# Quickstart validation: XDG configuration and neutral store default

Prerequisite: dev venv (`uv venv ~/.venvs/cc-cfp && uv pip install --python ~/.venvs/cc-cfp/bin/python -r cfp/requirements-dev.txt`).

## Automated

```bash
make test          # includes test_paths.py (SC-003 matrix), test_hook.py, seed clash tests
make test-hook
make lint-dashes
```

## Script-level scenarios (scratch HOME)

Run each with `env -i HOME=<scratch> PATH="$PATH"` so no real config is touched.

1. Neutral default (SC-001): `python3 -I cfp/scripts/cfp_store.py config show` reports `store` = `<scratch>/.local/share/cc-cfp/store`, `store_source` = `default`.
2. XDG variables: add `XDG_DATA_HOME=<scratch>/data XDG_CONFIG_HOME=<scratch>/cfg`; `config init --speaker-name T --seed-dir cfp/knowledge-base/profiles` writes `<scratch>/cfg/cc-cfp/config.json` and creates `<scratch>/data/cc-cfp/store`.
3. Legacy (SC-002): put `{"store": "<scratch>/old"}` in `<scratch>/.config/cc-cfp/config.json`, set `XDG_CONFIG_HOME=<scratch>/cfg`; `config show` reports `store_source` = `config` and `config_file` = the legacy path.
4. Relative variable: `CFP_STORE=talks config show` fails with `CFP_STORE must be an absolute path`.
5. Personal profile (SC-004): copy `cfp/knowledge-base/profiles/kubecon` to `<scratch>/.local/share/cc-cfp/profiles/acme-summit`, and another copy to `.../profiles/kubecon` with a later `seed_version`; `config init` on a fresh store seeds `acme-summit`, uses the user `kubecon`, and returns one clash warning.
6. Hook agreement (SC-003): for scenarios 1 to 4, pipe `{"prompt":"/cfp:status"}` into `python3 -I cfp/hooks/scripts/context-hook.py` with the same env; `<store>` equals `config show`'s `store`, or `<store-error>` matches the CLI error.

## Interactive (Claude Code session)

7. `/cfp:init` in a scratch HOME with two `~/Obsidian/<vault>` folders and a user `kubecon` variant in `<data folder>/profiles`: default is the XDG path (absolute), both vault `Talks` folders are offered, the `kubecon` clash warning appears exactly once, the report names the personal profiles folder.

## Docs (SC-005)

8. `rg -n -i "obsidian" README.md docs/guide/content specs/001-cfp-plugin/{spec.md,plan.md,research.md,contracts} cfp/skills/init/SKILL.md` shows no statement that the store defaults to an Obsidian vault without a pointer to feature 002.
