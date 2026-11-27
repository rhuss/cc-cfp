# Research: XDG Configuration and Neutral Store Default

## R1. Sharing resolution code between the hook and the CLI

**Decision**: New module `cfp/scripts/cfplib/paths.py`; the hook adds `<plugin-root>/scripts` to `sys.path` and imports it.

**Rationale**: FR-004 requires identical resolution. Today the hook duplicates the logic and already diverges (it does not expand `~` consistently and ignores XDG). `python3 -I` ignores `PYTHONPATH` but an explicit `sys.path.insert` works. The module only imports `os`, `json`, `pathlib`, and `cfplib.CfpError`, so the import cost is negligible.

**Alternatives considered**: keep two copies plus a parity test (rejected: drift is exactly the bug class FR-004 targets); have the hook shell out to `cfp_store.py config show` (rejected: a second interpreter start per prompt, closer to the 5 s timeout, and harder error mapping).

## R2. XDG Base Directory rules

**Decision**: `XDG_CONFIG_HOME` / `XDG_DATA_HOME` are used only when non-empty and absolute; otherwise `~/.config` / `~/.local/share`. No `XDG_CONFIG_DIRS` / `XDG_DATA_DIRS` search.

**Rationale**: matches the XDG spec ("If an implementation encounters a relative path in any of these variables it should consider the path invalid and ignore it"). The system-wide search lists add nothing for a single-user plugin.

**Alternatives considered**: macOS `~/Library/Application Support` (rejected in the spec assumptions); supporting `XDG_DATA_DIRS` for team profiles (deferred; `CFP_DATA_DIR` covers a shared folder).

## R3. `~` and relative values in cfp variables

**Decision**: `os.path.expanduser` on `CFP_CONFIG_DIR`, `CFP_DATA_DIR`, `CFP_STORE`; then reject non-absolute values with `CfpError("<VAR> must be an absolute path, got '<value>'")`. `--store` keeps today's behavior (resolved against the current folder).

**Rationale**: Claude Code `settings.json` `env` values are not shell-expanded, so `~/x` is a realistic input. The hook runs with an unpredictable working directory, so relative paths cannot be resolved consistently.

## R4. Legacy config fallback

**Decision**: read `~/.config/cc-cfp/config.json` only if `CFP_CONFIG_DIR` is unset and the resolved file does not exist. Never copy or delete the legacy file. Writes go to the resolved location.

**Rationale**: zero-step upgrade (SC-002) without touching user files. When `XDG_CONFIG_HOME` is unset the resolved and legacy paths are identical, so the common case has no fallback at all.

## R5. Seed override and version comparison

**Decision**: user seeds override plugin seeds by folder name. `seed_version` stays an ISO date string compared lexically (feature 001 behavior). Status entries gain `source` (`plugin`/`user`) and `seed_dir`.

**Rationale**: reuses the full feature 001 diff/update flow unchanged; the only new behavior is which folder a name maps to.

**Alternatives considered**: merging user files on top of shipped files per file (rejected: unclear ownership, the user asked for "my profile wins").

## R6. Where warnings travel

**Decision**: a top-level `warnings: [str]` list in the JSON result of `config init`, `profile seed-status`, and `profile seed-update` (empty list when none). The init skill de-duplicates by profile name across calls.

**Rationale**: stdout carries exactly one JSON object per call (feature 001 contract), so warnings must be part of it.

## R7. Hook error reporting

**Decision**: new `<store-error>` element, emitted only when resolution failed; `<store>` empty and `<store-initialized>false` in that case. The preamble shows the error and stops before offering init.

**Rationale**: putting the message into `<store>` would make skills use it as a path (spec review I3).
