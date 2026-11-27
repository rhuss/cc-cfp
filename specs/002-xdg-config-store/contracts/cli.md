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

A seed profile, shipped or personal, is exactly `profile.md`, `events/*.md` and `examples/*.md`; init copies those files as regular files and skips symlinked `events/` or `examples/` folders and files. A clash needs the exact same name. A user folder whose name differs from a shipped one only in case is skipped with a warning on every file system (on APFS and NTFS both names are one store folder). A seed whose store folder exists only under another case (for example a personal `ACME` and a store profile `acme` on APFS) is not copied by init, left out of seed-status and refused by seed-update, each with the warning `profile '<name>' from <dir> not used: the store already has '<existing>', ...`.

## `profile seed-status`

`{"seeds": [...], "warnings": [...]}`. Each seed entry adds `source` (`plugin`|`user`) and `seed_dir`. Diffs of user seeds use `user/<rel>` as target label. A seed whose store folder exists only under another case is left out of `seeds` with the `not used` warning. `--seed-dir` stays the plugin folder; optional `--user-seed-dir`. Fails on an invalid `CFP_DATA_DIR`.

## `profile seed-update`

Result adds `source` and `warnings`. A name present only in the user folder is accepted. Error text for an unknown profile: `no seed profile '<id>' in <plugin dir> or <user dir>`. A profile whose store folder exists only under another case is refused with the `not used` warning text. Refused before any write when the store's `profiles/` folder, the store profile folder, its `events/` or `examples/` folder, or a file to be written is a symlink (the write would change a file outside the store). Fails on an invalid `CFP_DATA_DIR`.
