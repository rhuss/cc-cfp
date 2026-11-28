# Data Model: XDG Configuration and Neutral Store Default

No store file format changes. The entities below are resolved locations and in-memory records.

## Config folder

| Field | Rule |
|-------|------|
| path | `CFP_CONFIG_DIR` (after `~` expansion, must be absolute) else `$XDG_CONFIG_HOME/cc-cfp` (if non-empty and absolute) else `~/.config/cc-cfp` |
| config file | `<path>/config.json`, JSON object; known key `store` (absolute path string); unknown keys preserved on write |
| legacy file | `~/.config/cc-cfp/config.json`, read only when `CFP_CONFIG_DIR` unset and `<path>/config.json` does not exist |

## Data folder

| Field | Rule |
|-------|------|
| path | `CFP_DATA_DIR` (after `~` expansion, must be absolute) else `$XDG_DATA_HOME/cc-cfp` (if non-empty and absolute) else `~/.local/share/cc-cfp` |
| `profiles/` | personal seed profiles; never created by cfp |
| `store/` | default store; created by init only when chosen |

## Store resolution result

| Field | Values |
|-------|--------|
| store | absolute path |
| source | `argument`, `environment`, `config`, `default` |
| config_file | path of the config file read, or `null` |
| config_write_path | path the next write goes to (always the resolved config file) |

## Seed entry

| Field | Rule |
|-------|------|
| name | folder name, must contain `profile.md` |
| dir | absolute folder path |
| source | `plugin` or `user` |

Collection rule: plugin entries first, then user entries; a user entry with the same name replaces the plugin entry and adds one warning: `profile '<name>': using <user dir> instead of the shipped <plugin dir>` (plus `; it has no seed_version, so it will not replace an existing store copy` when the user `profile.md` lacks `seed_version`).

## Seed status entry (extended)

Feature 001 fields (`profile`, `state`, `store_version`, `seed_version`, `files`, `error`) plus `source` and `seed_dir`. States unchanged: `missing`, `current`, `outdated`, `newer`, `local`, `unreadable`.
