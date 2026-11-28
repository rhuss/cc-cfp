# Feature Specification: XDG Configuration and Neutral Store Default

**Feature Branch**: `002-xdg-config-store`

**Created**: 2026-11-27

**Status**: Draft

**Input**: User description: "XDG-conformant configuration and neutral store default for the cfp plugin. (1) Config file location: $CFP_CONFIG_DIR, else $XDG_CONFIG_HOME/cc-cfp, else ~/.config/cc-cfp; config.json keeps the store path (existing file location stays compatible). (2) Store resolution: --store, then CFP_STORE env var, then config.json "store", then the neutral default $XDG_DATA_HOME/cc-cfp/store (fallback ~/.local/share/cc-cfp/store). /cfp:init no longer defaults to an Obsidian vault; detected ~/Obsidian/<vault>/Talks folders are still offered as additional choices, and init prints the full resolved path. (3) User-level conference profiles: a data directory $CFP_DATA_DIR, else $XDG_DATA_HOME/cc-cfp, else ~/.local/share/cc-cfp, with a profiles/ subfolder that acts as a second seed source next to the plugin's knowledge-base/profiles. init, profile seed-status and seed-update read both sources. When a user profile has the same name as a shipped one, the user profile wins and a warning is printed. (4) Voice profiles stay owned by cc-prose (no cfp voice folder); init keeps listing cc-prose voice names. Update README, docs guide (install page, commands reference) and existing spec references that name Obsidian as the default."

## Clarifications

### Session 2026-11-27

- Q: When `CFP_STORE` is set and the user picks a different path at init, what should happen? → A: Init saves the chosen path and warns that `CFP_STORE` overrides it in later sessions until the variable is removed.
- Q: How can a user see which config file, data folder, and store cfp is actually using? → A: `config show` reports the config file path, the data folder, the personal profiles folder, the resolved store, and the source of the store (argument, environment, config file, or default).
- Q: Should init create the data folder and its `profiles/` subfolder when they do not exist? → A: No. Init leaves them absent and names the personal profiles path in its report.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Neutral store default at first setup (Priority: P1)

A speaker installs cfp and runs `/cfp:init` for the first time. They do not use Obsidian, or they do not want their talk data inside their notes vault. Init proposes a store location that follows the platform's standard place for user data, shows the full path, and still lists any Obsidian vault folders it found as alternative choices.

**Why this priority**: The current default ties the plugin to one note-taking tool. Every new user meets this default on the first run, so it shapes the first impression and where all later data lands.

**Independent Test**: Run init in a home directory without `~/Obsidian` and without any cfp environment variables or config file. The proposed default is `~/.local/share/cc-cfp/store`, shown as a full path, and accepting it creates a working store.

**Acceptance Scenarios**:

1. **Given** no cfp configuration, no `XDG_DATA_HOME`, and no `~/Obsidian`, **When** the user runs `/cfp:init`, **Then** the proposed default is `~/.local/share/cc-cfp/store`, printed as an absolute path.
2. **Given** `XDG_DATA_HOME=/data/me` is set and nothing else is configured, **When** the user runs `/cfp:init`, **Then** the proposed default is `/data/me/cc-cfp/store`.
3. **Given** `~/Obsidian/work` and `~/Obsidian/private` exist, **When** the user runs `/cfp:init`, **Then** the neutral default is the first (recommended) choice and `~/Obsidian/work/Talks` and `~/Obsidian/private/Talks` are offered as further choices, plus free text.
4. **Given** `CFP_STORE=/elsewhere/talks` is set, **When** the user runs `/cfp:init`, **Then** `/elsewhere/talks` is the proposed default.
5. **Given** the user config file already names a store, **When** the user runs `/cfp:init` and the store is initialized, **Then** init shows that store and offers to keep it, re-run setup, or use a different path (behavior unchanged from feature 001).

---

### User Story 2 - Configuration follows the XDG layout and can be relocated (Priority: P1)

A speaker keeps dotfiles under version control and sets `XDG_CONFIG_HOME`, or wants cfp's settings in a specific folder (for example, a synced folder). cfp reads and writes its user config in the XDG config location, or in a folder named by a cfp-specific environment variable. Existing users whose config sits at `~/.config/cc-cfp/config.json` keep working without any action.

**Why this priority**: Without a predictable, overridable config location, the neutral store default (Story 1) can only be changed per command. Existing users must not lose their store setting.

**Independent Test**: Set `CFP_CONFIG_DIR` to an empty temp folder, run init, and confirm the config file is written there and later commands find the store through it, with no file written to `~/.config/cc-cfp`.

**Acceptance Scenarios**:

1. **Given** `CFP_CONFIG_DIR=/tmp/cfpconf`, **When** init completes, **Then** the store path is saved in `/tmp/cfpconf/config.json` and every later cfp command (scripts and the session context injection) resolves the store from that file.
2. **Given** `CFP_CONFIG_DIR` is unset and `XDG_CONFIG_HOME=/cfg`, **When** init completes, **Then** the config is saved in `/cfg/cc-cfp/config.json`.
3. **Given** neither variable is set, **When** init completes, **Then** the config is saved in `~/.config/cc-cfp/config.json`, the same place feature 001 used.
4. **Given** an existing `~/.config/cc-cfp/config.json` from feature 001 and `XDG_CONFIG_HOME` set to another folder that holds no cfp config, **When** any cfp command runs, **Then** the store from the existing file is still found, and the next write goes to the XDG location.
5. **Given** `--store`, `CFP_STORE`, and a config file each name a different store, **When** a cfp command runs, **Then** `--store` wins over `CFP_STORE`, which wins over the config file, which wins over the neutral default.

---

### User Story 3 - Personal conference profiles that survive plugin updates (Priority: P2)

A speaker regularly submits to conferences that the plugin does not ship (for example, an internal company summit). They keep their own profile folders in the cfp data folder. Init copies these into the store like shipped profiles, and the seed update check compares the store copy with their own version. If they keep their own variant of a shipped profile under the same name, their variant is used and cfp says so.

**Why this priority**: Valuable for repeat speakers and for anyone with more than one store, but the plugin works without it.

**Independent Test**: Place a profile folder `acme-summit/` with a `profile.md` in `~/.local/share/cc-cfp/profiles/`, run init on a fresh store, and confirm `acme-summit` is seeded and approved next to the shipped profiles.

**Acceptance Scenarios**:

1. **Given** `<data dir>/profiles/acme-summit/profile.md` exists, **When** init runs on a store without that profile, **Then** `acme-summit` is copied into the store, marked approved, and listed in the seeded profiles of the report.
2. **Given** `<data dir>/profiles/kubecon/` exists next to the shipped `kubecon` profile, **When** init, seed-status, or seed-update runs, **Then** the user's `kubecon` is used as the seed and a warning names the profile and both locations.
3. **Given** the user's own profile carries a `seed_version` and the user raises it after the profile was seeded, **When** the user runs `/cfp:init`, **Then** the seed status reports the store copy as outdated and offers the same diff-and-update flow as for shipped profiles.
4. **Given** `CFP_DATA_DIR=/team/cfp` is set, **When** init runs, **Then** profiles are read from `/team/cfp/profiles/` and not from the XDG data folder, and the proposed default store is `/team/cfp/store`.
5. **Given** no data folder or no `profiles/` subfolder exists, **When** init runs, **Then** only shipped profiles are seeded and no warning or error appears.

---

### User Story 4 - Documentation matches the new defaults (Priority: P3)

A reader of the README or the published guide learns the new default store location, the config and data folder locations with their environment variables, and how to add personal profiles. No document still describes the Obsidian vault as the default.

**Why this priority**: Required for a consistent release, but it follows the behavior changes.

**Independent Test**: Search the documents listed in FR-017 for statements that the store defaults to an Obsidian vault. None remain unannotated.

**Acceptance Scenarios**:

1. **Given** the feature is complete, **When** a reader opens the install page of the guide, **Then** it states the default store path, the resolution order, both folder locations with their environment variables, and that Obsidian vaults are offered as choices.
2. **Given** the feature is complete, **When** a reader opens the commands reference for `/cfp:init`, **Then** the default path rule matches Story 1.

---

### Edge Cases

- `XDG_CONFIG_HOME` or `XDG_DATA_HOME` holds a relative path or is empty: it is ignored and the standard fallback under the home folder is used, as the XDG Base Directory specification requires.
- `CFP_CONFIG_DIR`, `CFP_DATA_DIR`, or `CFP_STORE` holds a relative path after `~` expansion: it is rejected with an error that names the variable, instead of being resolved against the current folder (which differs between sessions). A relative `--store` argument is resolved against the current folder, since the user typed it there.
- The neutral default store folder does not exist yet: init creates it including missing parent folders; commands other than init report the store as not initialized and point to `/cfp:init`, as today.
- The config file at the resolved location exists but is malformed or has no `store` entry: it is treated as having no store entry (as today), the legacy fallback is NOT consulted, and init overwrites it with a valid file.
- A folder in `<data dir>/profiles/` has no `profile.md`: it is skipped silently, the same rule that applies to shipped seeds.
- A user profile and a shipped profile share a name, and the store copy came from the shipped one: the seed status compares the store copy with the user's version. Only the state `outdated` (user version higher) leads to the diff-and-update flow. When the user version is lower, the state is `newer` and init says that the store copy's `seed_version` is higher than the user's profile, so nothing is offered. Nothing is replaced without confirmation.
- A user variant of a shipped profile has no `seed_version`: it never replaces an existing store copy, and the clash warning says so. To have a variant offered over an existing shipped copy, its `seed_version` must be later than the shipped one.
- More than three Obsidian vaults exist: init offers the first three vault folders (sorted by name) as choices; others can be entered through the free-text option.
- `seed-update` is asked for a profile that exists only in the user data folder: it works the same as for a shipped profile.
- A user profile has no `seed_version`: it is seeded once, its store copy counts as local, and it is never offered an update. To get update offers later, the user adds a `seed_version` to their profile before the first seeding.
- Both sources are missing or the plugin seed folder is missing: the existing error for a missing seed folder still applies to the plugin's folder; a missing user folder is never an error.
- The user picks an Obsidian vault folder at init: everything works as in feature 001; only the default changed.

## Requirements *(mandatory)*

### Functional Requirements

**Config location**

- **FR-001**: cfp MUST determine its config folder in this order: the `CFP_CONFIG_DIR` environment variable, then `$XDG_CONFIG_HOME/cc-cfp`, then `~/.config/cc-cfp`. The config file inside it is `config.json`.
- **FR-002**: `XDG_CONFIG_HOME` and `XDG_DATA_HOME` MUST be ignored when empty or not absolute. Empty or whitespace-only `CFP_*` values count as unset. A leading `~` in `CFP_CONFIG_DIR`, `CFP_DATA_DIR`, and `CFP_STORE` MUST be expanded first; if the value is still relative, the command MUST fail with an error naming the variable. Store resolution stops at the first step that yields a store, so a `CFP_STORE` or `CFP_CONFIG_DIR` error affects every command whose store resolution reaches that variable (an explicit `--store` reaches neither); a `CFP_DATA_DIR` error affects only commands that read the data folder (init, seed status, seed update, `config show`) and the default store fallback.
- **FR-002a**: The session context injection cannot stop a session. When store resolution fails, it MUST leave the store path empty, report the store as not initialized, and add a separate store error entry with the message. The shared skill preamble MUST show that error to the user and stop before offering `/cfp:init`, and its description of the store entry MUST be updated (after this feature the store path is empty only on error).
- **FR-003**: When no config file exists at the resolved location and `CFP_CONFIG_DIR` is not set, cfp MUST read `~/.config/cc-cfp/config.json` as a legacy fallback. A resolved file that exists but is malformed or has no `store` entry never triggers the fallback. Writes always go to the resolved location.
- **FR-004**: Every component that resolves the store (the command scripts and the session context injection) MUST use the same config folder and store resolution rules, so they never disagree about the active store.

**Store location**

- **FR-005**: cfp MUST resolve the store in this order: the `--store` argument, the `CFP_STORE` environment variable, the `store` entry of the config file, then the neutral default `<data folder>/store`, with the data folder from FR-009 (so `$XDG_DATA_HOME/cc-cfp/store`, or `~/.local/share/cc-cfp/store` when `XDG_DATA_HOME` is unusable, unless `CFP_DATA_DIR` is set).
- **FR-006**: `/cfp:init` MUST propose as default the store that FR-005 resolves without `--store`, and print it as an absolute path.
- **FR-007**: `/cfp:init` MUST NOT use an Obsidian vault as the default. When `~/Obsidian/<vault>` folders exist, it MUST offer `~/Obsidian/<vault>/Talks` as additional choices next to the default and a free-text option, at most three vaults (sorted by name); further vaults can be typed into the free-text option.
- **FR-008**: Init MUST create the chosen store folder including missing parents, and save the chosen path to the config file at the location from FR-001. When `CFP_STORE` is set and differs from the chosen path, init MUST warn that `CFP_STORE` overrides the saved path in later sessions.
- **FR-008a**: `config show` MUST report the config file actually read (or none), the config file the next write goes to, the data folder, the personal profiles folder, the resolved store, and the source of the store (`argument`, `environment`, `config`, or `default`).

**Data folder and user profiles**

- **FR-009**: cfp MUST determine its data folder in this order: `CFP_DATA_DIR`, then `$XDG_DATA_HOME/cc-cfp`, then `~/.local/share/cc-cfp`.
- **FR-010**: The `profiles/` subfolder of the data folder MUST act as a second seed source next to the plugin's shipped profiles, with the same folder format and the same rule that a seed is a folder holding `profile.md`.
- **FR-011**: Init (seeding a new store), seed status, and seed update MUST consider both seed sources. The command scripts MUST locate the personal profiles folder themselves from FR-009 (an explicit override argument for tests is allowed); callers pass only the plugin seed folder as today. A missing data folder or `profiles/` subfolder MUST be treated as an empty source without warning. Init MUST NOT create the data folder or `profiles/` (except the default store inside it when chosen) and MUST name the personal profiles path in its report.
- **FR-012**: When a user profile and a shipped profile have the same name, the user profile MUST be used as the seed. Every script command that reads seeds MUST include one warning per clashing profile in a `warnings` list of its result, naming the profile and both locations. `/cfp:init` MUST show each clash once per run, even though it calls several such commands. A clash needs the exact same name; a user folder whose name differs from a shipped one only in case MUST be skipped with a warning on every file system, because on case-insensitive file systems (APFS, NTFS) both names are one store folder. Profile names are case-insensitive on every file system: a seed whose name differs from an existing store profile only in case MUST NOT be copied, compared, or updated, and every seed command MUST report it with a warning.
- **FR-013**: Seeding, status comparison, and updates of user profiles MUST follow the rules of feature 001 for shipped profiles: seeded copies are marked approved, store profiles without a seed version are never replaced, updates replace whole files only after the user chooses, and files only the store has are never touched. Consequently, only a user profile that carries a `seed_version` takes part in update checks; one without it is copied once and its store copy counts as local from then on. `seed_version` values are ISO dates (`YYYY-MM-DD`), as in the feature 001 store file contract, because versions are compared in that form. The guide MUST state both rules for authors of personal profiles, and that a variant of a shipped profile needs a later `seed_version` than the shipped one to be offered.
- **FR-014**: The seed status output MUST state for each seed its source (`plugin` or `user`) and the folder it was read from, so the init skill can show it.

**Voice profiles**

- **FR-015**: cfp MUST NOT introduce its own voice profile folder. Init MUST keep listing the named voice profiles that cc-prose provides, as in feature 001.

**Documentation**

- **FR-016**: The README, the guide's install page, and the guide's commands reference MUST describe the neutral default store, the store resolution order, the config and data folder locations with their environment variables, and how to add personal profiles.
- **FR-017**: Statements that name the Obsidian vault as the default store MUST be updated in the README, the guide sources, and `cfp/skills/init/SKILL.md`, and annotated to point to this feature in the feature 001 `spec.md`, `plan.md`, `research.md`, and `contracts/`. Historical records of feature 001 (`tasks.md`, review findings, smoke test and quickstart results, checklists) stay unchanged. Statements that Obsidian can open and edit the store stay, since they remain true.

### Key Entities

- **Config folder**: Where cfp keeps user settings. Holds `config.json` with the store path. Location set by FR-001.
- **Data folder**: Where cfp keeps user data that is not tied to one store. Holds `profiles/` and the default `store/` (FR-005). Location set by FR-009.
- **Seed source**: A folder of profile folders that init copies into a store. There are two: the plugin's shipped profiles and the user's `profiles/`. Each seed has a name (its folder name) and a source label.
- **Store**: The user's markdown data (profiles, talks, proposals, bios, resources). Unchanged in format; only its default location changes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a machine without Obsidian and without any cfp configuration, a new user completes `/cfp:init` by accepting every default, and the store ends up at the XDG data location with no manual path entry.
- **SC-002**: A user who completed setup under feature 001 (config at `~/.config/cc-cfp/config.json`) runs any cfp command after upgrading and reaches the same store with zero manual migration steps.
- **SC-003**: For every combination of `CFP_STORE` (set or unset), config file location (`CFP_CONFIG_DIR`, `XDG_CONFIG_HOME`, home default, legacy fallback), and store entry in that file (present or absent), 16 combinations in total, with `CFP_DATA_DIR` both unset and set, the command scripts run without `--store` and the session context report the same store path. With `--store` given, the scripts use it in every one of these combinations.
- **SC-004**: A personal profile placed in the data folder appears in a freshly initialized store after one init run, and each profile name clash with a shipped profile is shown to the user exactly once per `/cfp:init` run.
- **SC-005**: Searching the documents listed in FR-017 for an Obsidian vault described as the default store returns no unannotated match.

## Assumptions

- macOS users accept XDG paths (`~/.config`, `~/.local/share`) instead of `~/Library/Application Support`, as most command-line tools do; the environment variables cover users who want something else.
- A hidden default store folder is acceptable because init prints the absolute path and the user can choose a visible folder or an Obsidian vault at the same prompt.
- Existing stores are not moved. Changing the default only affects users who run init without a configured store.
- User profiles use exactly the same file format as shipped profiles (feature 001 store file contracts); this feature adds no new profile fields.
- The legacy fallback in FR-003 is kept indefinitely; it costs one extra file check and is the only migration path.
- cc-prose remains the only owner of voice profiles; how cc-prose locates them is out of scope.
