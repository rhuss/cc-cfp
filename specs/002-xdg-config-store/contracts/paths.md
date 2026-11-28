# Contract: `cfplib/paths.py`

All functions accept keyword `env` (mapping, default `os.environ`) and `home` (`Path`, default `Path.home()`). They never create folders.

Common rules:

- Empty or whitespace-only `CFP_CONFIG_DIR`, `CFP_DATA_DIR`, `CFP_STORE` count as unset (an empty `CFP_CONFIG_DIR` therefore keeps the legacy fallback).
- `CFP_*` values get `~` expansion, then must be absolute, else `CfpError("<VAR> must be an absolute path, got '<value>'")`.
- `XDG_CONFIG_HOME` / `XDG_DATA_HOME` are used only when non-empty and absolute; otherwise ignored.
- The `store` value in `config.json` is used when it is a non-empty string; it gets `~` expansion; a relative value is resolved against the config file's folder; a non-string value counts as absent.

| Function | Returns | Errors (`CfpError`) |
|----------|---------|---------------------|
| `config_dir(env, home)` | `Path` per data-model "Config folder" | `CFP_CONFIG_DIR must be an absolute path, got '<v>'` |
| `config_file(env, home)` | `config_dir() / "config.json"` | as above |
| `legacy_config_file(home)` | `home / ".config/cc-cfp/config.json"` | none |
| `read_config(env, home)` | `(data: dict, read_path: Path or None)`; malformed or non-object file gives `({}, path)`; missing resolved file falls back to legacy only when `CFP_CONFIG_DIR` is unset | as `config_dir` |
| `data_dir(env, home)` | `Path` per data-model "Data folder" | `CFP_DATA_DIR must be an absolute path, got '<v>'` |
| `user_profiles_dir(env, home)` | `data_dir() / "profiles"` | as `data_dir` |
| `default_store(env, home)` | `data_dir() / "store"` | as `data_dir` |
| `resolve_store(cli_store, env, home)` | `(Path, source)`; `cli_store` expanded and resolved against cwd | `CFP_STORE ...`, plus errors of the steps actually reached |

Evaluation is lazy: resolution stops at the first step that yields a store, so `--store` never reads the variables of later steps, and a valid `CFP_STORE` never reads `CFP_CONFIG_DIR` or `CFP_DATA_DIR`.
