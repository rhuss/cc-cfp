"""User-level and store-level configuration.

User config: ``config.json`` in the config folder (``CFP_CONFIG_DIR``, else
``$XDG_CONFIG_HOME/cc-cfp``, else ``~/.config/cc-cfp``, with the feature 001
file as a read-only legacy fallback), holding ``{"store": path}``. All
location rules live in ``cfplib.paths``; this module only reads and writes.
Store config: ``<store>/config.md`` front matter (speaker name, company,
voice profile, review rounds, default profile).
"""

import json
import os
import shutil
import stat
import tempfile
from pathlib import Path

from cfplib import CfpError, frontmatter, fsutil, paths, seeds
from cfplib import store as store_module

STORE_DIRS = ("profiles", "talks", "proposals", "bios", "resources")
DEFAULT_STORE_CONFIG = {
    "speaker_name": "",
    "speaker_company": "",
    "voice_profile": "",
    "review_rounds": 3,
    "default_profile": "",
}
INT_KEYS = {"review_rounds"}


def write_user_config(store):
    """Save the store path, keeping unknown keys of the file that was read."""
    path = paths.config_file()
    data = dict(paths.read_config()[0])
    data["store"] = str(Path(store).expanduser().resolve())
    # Atomic, so a crash or a full disk never leaves a truncated config.json (which would silently
    # send every later command to the default store); a symlinked config.json keeps its link.
    fsutil.write_text_atomic(path, json.dumps(data, indent=2) + "\n")
    return path


def resolve_store(cli_store):
    """Resolution order: --store, CFP_STORE, the config file, then ``<data folder>/store``."""
    return paths.resolve_store(cli_store)[0]


def store_config_path(store):
    return Path(store) / "config.md"


def require_store(store):
    """Ensure the store exists and is initialized; return it as a Path."""
    store = Path(store)
    if not paths.store_initialized(store):  # raises on an access error instead of claiming "not initialized"
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
    """Copy a seed profile into the store as regular files and mark it approved.

    Only the files ``seeds.seed_files`` lists are copied, so symlinked
    ``events/`` or ``examples/`` folders and files are skipped and the store
    copy never links back to the seed (a later store write would otherwise
    change the user's own file). The seed's ``profile.md`` is parsed before
    anything is written, so a broken seed raises an error that names the
    seed file. The copy is built in a unique hidden sibling folder and
    renamed into place, so a failure never leaves a partial profile behind.
    Returns False when another init created the profile folder first.
    """
    meta, body = frontmatter.load(seed_profile_dir / seeds.PROFILE_FILE)
    meta["approved"] = True
    meta["seed_version"] = str(meta.get("seed_version") or "")
    # A unique hidden sibling per call, so two inits running at once never share or delete each other's copy.
    staging = Path(tempfile.mkdtemp(prefix=f".{target_dir.name}.", suffix=".seeding", dir=target_dir.parent))
    try:
        os.chmod(staging, stat.S_IMODE(target_dir.parent.stat().st_mode))  # mkdtemp creates it private (0700)
        for rel in seeds.seed_files(seed_profile_dir):
            if rel == seeds.PROFILE_FILE:
                continue
            destination = staging / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((seed_profile_dir / rel).read_bytes())
        frontmatter.save(staging / seeds.PROFILE_FILE, meta, body)
        try:
            os.replace(staging, target_dir)
        except OSError:
            if not target_dir.is_dir():
                raise
            # Another init filled the profile folder after our exists() check (ENOTEMPTY or EEXIST):
            # keep its copy and drop ours.
            shutil.rmtree(staging, ignore_errors=True)
            return False
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return True


def init_store(store, values, seed_dir=None, user_seed_dir=None):
    """Create the folder tree, config.md, user config, and seed profiles.

    Seeds come from the plugin's ``seed_dir`` and the user's own
    ``user_seed_dir`` (``None`` means no user source, a missing folder is an
    empty one). A user profile replaces a shipped one of the same name; the
    result lists one warning per such clash.
    """
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
    entries, warnings = seeds.collect(seed_dir or None, user_seed_dir)
    for entry in entries:
        target = store / "profiles" / entry["name"]
        if target.exists() or target.is_symlink():
            existing = store_module.case_alias(target.parent, target.name)
            if existing is not None:
                # On APFS or NTFS 'Acme' and 'acme' are one folder; say so instead of skipping silently.
                warnings.append(seeds.alias_warning(entry, existing))
            continue
        try:
            if not _seed_profile(entry["dir"], target):
                continue  # a concurrent init seeded it
        except (CfpError, OSError) as error:
            if entry["source"] != "user":
                raise
            # A hand-written personal profile must not stop the setup; the user fixes it and runs init again.
            warnings.append(f"profile '{entry['name']}' from {entry['dir']} skipped: {error}")
            continue
        seeded.append(entry["name"])
        created.append(str(target))

    current = load_store_config(store)
    if not current.get("default_profile"):
        profiles = store_module.list_profile_ids(store)
        if profiles:
            write_store_config(store, {"default_profile": profiles[0]})

    config_write_path = write_user_config(store)
    return {
        "store": str(store),
        "created": created,
        "seeded_profiles": seeded,
        "config_write_path": str(config_write_path),
        "warnings": warnings,
    }
