# Contract: changed CLI outputs

Only additions; every existing field keeps its meaning. Key names are the same everywhere: `config_file` is the file that was read, `config_write_path` is the file that was or will be written.

## `config show`

```json
{
  "ok": true,
  "store": "/home/me/.local/share/cc-cfp/store",
  "store_source": "default",
  "exists": false,
  "config": {"speaker_name": "", "...": "..."},
  "config_file": null,
  "config_write_path": "/home/me/.config/cc-cfp/config.json",
  "data_dir": "/home/me/.local/share/cc-cfp",
  "user_profiles_dir": "/home/me/.local/share/cc-cfp/profiles"
}
```

`config_file` is `null` when no file was read. An invalid `CFP_DATA_DIR` (or `CFP_CONFIG_DIR`) makes the call fail with `ok: false` and the variable's error.

## `config init`

Adds `warnings: [str]`, `config_write_path` (the file written), and `user_profiles_dir`. Warnings: seed clashes (see data-model), and `CFP_STORE is set to '<x>' and overrides the saved store '<y>' in later sessions` when the expanded, resolved `CFP_STORE` differs from the chosen store. Seeds from both sources; `seeded_profiles` unchanged in shape. Fails on an invalid `CFP_DATA_DIR`.

Optional hidden argument `--user-seed-dir <path>` (tests) overrides `user_profiles_dir`.

## `profile seed-status`

`{"seeds": [...], "warnings": [...]}`. Each seed entry adds `source` (`plugin`|`user`) and `seed_dir`. Diffs of user seeds use `user/<rel>` as target label. `--seed-dir` stays the plugin folder; optional `--user-seed-dir`. Fails on an invalid `CFP_DATA_DIR`.

## `profile seed-update`

Result adds `source` and `warnings`. A name present only in the user folder is accepted. Error text for an unknown profile: `no seed profile '<id>' in <plugin dir> or <user dir>`. Fails on an invalid `CFP_DATA_DIR`.
