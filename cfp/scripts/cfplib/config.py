"""User-level and store-level configuration.

User config: ``config.json`` in the config folder (``CFP_CONFIG_DIR``, else
``$XDG_CONFIG_HOME/cc-cfp``, else ``~/.config/cc-cfp``, with the feature 001
file as a read-only legacy fallback), holding ``{"store": path}``. All
location rules live in ``cfplib.paths``; this module only reads and writes.
Store config: ``<store>/config.md`` front matter (speaker name, company,
voice profile, review rounds, default profile).
"""

import json
import shutil
from pathlib import Path

from cfplib import CfpError, frontmatter, paths

STORE_DIRS = ("profiles", "talks", "proposals", "bios", "resources")
DEFAULT_STORE_CONFIG = {
    "speaker_name": "",
    "speaker_company": "",
    "voice_profile": "",
    "review_rounds": 3,
    "default_profile": "",
}
INT_KEYS = {"review_rounds"}


def user_config_path():
    """The config file the next write goes to (it may not exist yet)."""
    return paths.config_file()


def load_user_config():
    """Return the user config dict in effect, or {} when missing or malformed."""
    return paths.read_config()[0]


def write_user_config(store):
    """Save the store path, keeping unknown keys of the file that was read."""
    path = paths.config_file()
    data = dict(paths.read_config()[0])
    path.parent.mkdir(parents=True, exist_ok=True)
    data["store"] = str(Path(store).expanduser().resolve())
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def resolve_store_with_source(cli_store):
    """Return ``(store, source)``; see ``cfplib.paths.resolve_store``."""
    return paths.resolve_store(cli_store)


def resolve_store(cli_store):
    """Resolution order: --store, CFP_STORE, the config file, then ``<data folder>/store``."""
    return paths.resolve_store(cli_store)[0]


def store_config_path(store):
    return Path(store) / "config.md"


def require_store(store):
    """Ensure the store exists and is initialized; return it as a Path."""
    store = Path(store)
    if not store_config_path(store).is_file():
        raise CfpError(
            f"store not initialized at {store}: run 'config init --store {store} --speaker-name <name>' (or /cfp:init)"
        )
    return store


def load_store_config(store):
    require_store(store)
    meta, _ = frontmatter.load(store_config_path(store))
    merged = dict(DEFAULT_STORE_CONFIG)
    for key, value in meta.items():
        merged[key] = value if value is not None else merged.get(key, "")
    for key in INT_KEYS:
        try:
            merged[key] = int(merged[key])
        except (TypeError, ValueError):
            merged[key] = DEFAULT_STORE_CONFIG[key]
    return merged


def write_store_config(store, values):
    merged = dict(DEFAULT_STORE_CONFIG)
    existing_path = store_config_path(store)
    body = ""
    if existing_path.is_file():
        meta, body = frontmatter.load(existing_path)
        merged.update(meta)
    for key, value in values.items():
        if value is None:
            continue
        merged[key] = value
    for key in INT_KEYS:
        try:
            merged[key] = int(merged[key])
        except (TypeError, ValueError):
            merged[key] = DEFAULT_STORE_CONFIG[key]
    frontmatter.save(existing_path, merged, body)
    return existing_path


def set_store_config(store, key, value):
    require_store(store)
    if key in INT_KEYS:
        try:
            value = int(value)
        except (TypeError, ValueError):
            raise CfpError(f"{key} must be an integer, got {value!r}")
    write_store_config(store, {key: value})
    return value


def _seed_profile(seed_profile_dir, target_dir):
    """Copy a seed profile directory into the store and mark it approved.

    Symlinks are copied as links, never followed, so a stray link in a seed
    directory cannot pull foreign files into the store.
    """
    shutil.copytree(seed_profile_dir, target_dir, symlinks=True)
    profile_file = target_dir / "profile.md"
    if profile_file.is_file():
        meta, body = frontmatter.load(profile_file)
        meta["approved"] = True
        meta["seed_version"] = str(meta.get("seed_version") or "")
        frontmatter.save(profile_file, meta, body)


def init_store(store, values, seed_dir=None):
    """Create the folder tree, config.md, user config, and seed profiles."""
    store = Path(store).expanduser().resolve()
    created = []
    for sub in ("",) + STORE_DIRS:
        path = store / sub if sub else store
        if not path.exists():
            path.mkdir(parents=True)
            created.append(str(path))
    config_file = store_config_path(store)
    existed = config_file.is_file()
    write_store_config(store, {k: v for k, v in values.items() if v is not None})
    if not existed:
        created.append(str(config_file))

    seeded = []
    if seed_dir:
        seed_dir = Path(seed_dir)
        if not seed_dir.is_dir():
            raise CfpError(f"seed directory not found: {seed_dir}")
        for entry in sorted(seed_dir.iterdir()):
            if not entry.is_dir() or not (entry / "profile.md").is_file():
                continue
            target = store / "profiles" / entry.name
            if target.exists():
                continue
            _seed_profile(entry, target)
            seeded.append(entry.name)
            created.append(str(target))

    current = load_store_config(store)
    if not current.get("default_profile"):
        profiles = sorted(p.name for p in (store / "profiles").iterdir() if (p / "profile.md").is_file())
        if profiles:
            write_store_config(store, {"default_profile": profiles[0]})

    write_user_config(store)
    return {"store": str(store), "created": created, "seeded_profiles": seeded}
