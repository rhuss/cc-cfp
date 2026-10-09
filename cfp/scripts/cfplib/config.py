"""User-level and store-level configuration.

User config: ``~/.config/cc-cfp/config.json`` holding ``{"store": path}``.
Store config: ``<store>/config.md`` front matter (speaker name, company,
voice profile, review rounds, default profile).
"""

import json
import os
import shutil
from pathlib import Path

from cfplib import CfpError, frontmatter

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
    return Path.home() / ".config" / "cc-cfp" / "config.json"


def load_user_config():
    """Return the user config dict, or {} when missing or malformed."""
    try:
        data = json.loads(user_config_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def write_user_config(store):
    path = user_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = load_user_config()
    data["store"] = str(Path(store).expanduser().resolve())
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def resolve_store(cli_store):
    """Resolution order: --store, env CFP_STORE, user config file."""
    candidate = cli_store or os.environ.get("CFP_STORE", "").strip() or load_user_config().get("store", "")
    if not candidate:
        raise CfpError(
            "no store configured: pass --store, set CFP_STORE, or run 'config init' (or /cfp:init)"
        )
    return Path(candidate).expanduser().resolve()


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
