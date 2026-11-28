# Brainstorm: XDG configuration and neutral store default

**Date:** 2026-11-27
**Status:** spec created (specs/002-xdg-config-store)

## Problem

`/cfp:init` proposes `~/Obsidian/<vault>/Talks` as the default store, which ties the plugin to one note-taking tool. The user config path `~/.config/cc-cfp/config.json` is hardcoded in two places (scripts and the session context hook) and ignores `XDG_CONFIG_HOME`. There is no place for personal conference profiles that should survive plugin updates and be reused across stores.

## Decisions

- Config folder: `CFP_CONFIG_DIR`, else `$XDG_CONFIG_HOME/cc-cfp`, else `~/.config/cc-cfp`. The existing `~/.config/cc-cfp/config.json` keeps working.
- Store resolution: `--store`, `CFP_STORE`, config `store`, then the neutral default `<data folder>/store` (by default `~/.local/share/cc-cfp/store`).
- Init no longer defaults to Obsidian; detected vault `Talks` folders stay as extra choices.
- Data folder: `CFP_DATA_DIR`, else `$XDG_DATA_HOME/cc-cfp`, else `~/.local/share/cc-cfp`. Its `profiles/` subfolder is a second seed source.
- Name clash between a user profile and a shipped profile: the user profile wins, with a warning.
- Voice profiles stay owned by cc-prose. No cfp voice folder.

## Approaches considered

- `~/.config/share`: not part of the XDG spec; rejected in favor of the config/data split.
- Visible default store `~/cfp`: rejected by the user in favor of the XDG data folder, since init prints the full path and offers alternatives.
- cfp-owned voice folder with inlined YAML for the humanizer: rejected; cc-prose already resolves voices by name and other tools share them.
