"""Seed profiles: compare them with the store copies and update outdated ones.

Seeds come from two sources: the profiles the plugin ships (``plugin``) and
the user's personal profiles in ``<data folder>/profiles`` (``user``). A user
profile with the same name as a shipped one replaces it, with a warning.

``config init`` copies a seed profile into a store once and never touches it
again. A later version of a seed is marked by a higher ``seed_version`` in
its ``profile.md``. ``status`` reports that with a diff per seed file, and
``update`` replaces the files the user chose while keeping their approval
flags. Files that exist only in the store (the user's own events, examples
of accepted proposals) are never read or written here.
"""

import difflib
from pathlib import Path

from cfplib import CfpError, frontmatter, store

PROFILE_FILE = "profile.md"
SEED_SUBDIRS = ("events", "examples")
# Besides profile.md, files under these directories carry an approval flag.
APPROVED_PREFIXES = ("events/",)
DIFF_LABELS = {"plugin": "shipped", "user": "user"}


def _profile_folders(seed_dir):
    return [entry for entry in sorted(Path(seed_dir).iterdir()) if entry.is_dir() and (entry / PROFILE_FILE).is_file()]


def _seed_profiles(seed_dir):
    seed_dir = Path(seed_dir)
    if not seed_dir.is_dir():
        raise CfpError(f"seed directory not found: {seed_dir}")
    return _profile_folders(seed_dir)


def _has_seed_version(seed_profile_dir):
    try:
        meta, _ = frontmatter.load(seed_profile_dir / PROFILE_FILE)
    except CfpError:
        return True  # broken front matter is reported when the seed is used; no extra claim here
    return bool(meta.get("seed_version"))


def collect(plugin_dir, user_dir=None):
    """Return ``(entries, warnings)`` for the seeds of both sources.

    Entries are ``{"name", "dir", "source"}``: the plugin's seeds first (a
    missing ``plugin_dir`` is an error; ``None`` means no plugin source), then
    the user's own profiles. A user profile with the name of a shipped one
    takes its place and adds one warning. A missing ``user_dir`` (or ``None``)
    is an empty source.
    """
    entries = []
    if plugin_dir is not None:
        entries = [{"name": entry.name, "dir": entry, "source": "plugin"} for entry in _seed_profiles(plugin_dir)]
    warnings = []
    if user_dir is not None and Path(user_dir).is_dir():
        index = {entry["name"]: i for i, entry in enumerate(entries)}
        for folder in _profile_folders(user_dir):
            try:
                store.check_id(folder.name, "profile id")
            except CfpError:
                # The folder name becomes a store path and a skill's shell argument, so it must be a safe id.
                warnings.append(
                    f"profile folder '{folder.name}' in {user_dir} skipped: "
                    "a profile name starts with a letter or digit and uses only letters, digits, '.', '_', and '-'"
                )
                continue
            user_entry = {"name": folder.name, "dir": folder, "source": "user"}
            if folder.name in index:
                shipped = entries[index[folder.name]]["dir"]
                warning = f"profile '{folder.name}': using {folder} instead of the shipped {shipped}"
                if not _has_seed_version(folder):
                    warning += "; it has no seed_version, so it will not replace an existing store copy"
                warnings.append(warning)
                entries[index[folder.name]] = user_entry
            else:
                entries.append(user_entry)
    return entries, warnings


def seed_files(seed_profile_dir):
    """Relative paths of the files a seed ships: profile.md, events/*.md, examples/*.md.

    These are exactly the files ``config init`` copies. Symlinked event and
    example files or folders are skipped, so a stray link in a seed directory
    cannot pull foreign files into the store; ``profile.md`` is read through
    a link. The store copy is always made of regular files.
    """
    files = [PROFILE_FILE]
    for sub in SEED_SUBDIRS:
        directory = seed_profile_dir / sub
        if directory.is_symlink() or not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.md")):
            if path.is_file() and not path.is_symlink():
                files.append(f"{sub}/{path.name}")
    return files


def _canonical(path):
    """The file as the store would write it, without its approval flag.

    Comparing this form keeps quoting, comments, and the approval of a copy
    out of the diff, so only real differences show up.
    """
    meta, body = frontmatter.load(path)
    meta.pop("approved", None)
    return frontmatter.dump(meta, body)


def _diff(store_text, seed_text, rel, source="plugin"):
    lines = difflib.unified_diff(
        store_text.splitlines(),
        seed_text.splitlines(),
        fromfile=f"store/{rel}",
        tofile=f"{DIFF_LABELS[source]}/{rel}",
        lineterm="",
        n=2,
    )
    return "\n".join(lines)


def _file_states(seed_profile_dir, target_dir, source="plugin"):
    files = []
    for rel in seed_files(seed_profile_dir):
        target = target_dir / rel
        if not target.is_file():
            files.append({"path": rel, "state": "missing"})
            continue
        seed_text = _canonical(seed_profile_dir / rel)
        try:
            store_text = _canonical(target)
        except CfpError as error:
            files.append({"path": rel, "state": "changed", "diff": f"(the store file cannot be read: {error})"})
            continue
        if store_text == seed_text:
            files.append({"path": rel, "state": "same"})
        else:
            files.append({"path": rel, "state": "changed", "diff": _diff(store_text, seed_text, rel, source)})
    return files


def _profile_status(store_path, seed_profile_dir, source="plugin"):
    profile_id = seed_profile_dir.name
    info = {"profile": profile_id, "state": "", "store_version": None, "seed_version": None, "files": []}
    try:
        seed_meta, _ = frontmatter.load(seed_profile_dir / PROFILE_FILE)
    except CfpError as error:
        # A broken seed (typically a hand-written personal profile) must not hide the other seeds.
        info["state"] = "unreadable"
        info["error"] = str(error)
        return info
    seed_version = str(seed_meta.get("seed_version") or "")
    info["seed_version"] = seed_version
    target_dir = store.profile_dir(store_path, profile_id)
    target = target_dir / PROFILE_FILE
    if not target.is_file():
        info["state"] = "missing"  # config init copies it
        return info
    try:
        store_meta, _ = frontmatter.load(target)
    except CfpError as error:
        info["state"] = "unreadable"
        info["error"] = str(error)
        return info
    store_version = str(store_meta.get("seed_version") or "")
    info["store_version"] = store_version
    if not store_version:
        info["state"] = "local"  # researched or hand-written, not a copy of a seed
    elif not seed_version or store_version == seed_version:
        info["state"] = "current"
    elif store_version < seed_version:  # ISO dates compare as strings
        info["state"] = "outdated"
        info["files"] = _file_states(seed_profile_dir, target_dir, source)
    else:
        info["state"] = "newer"  # the store copy came from a later seed than this one
    return info


def _entry_status(store_path, entry):
    info = _profile_status(store_path, entry["dir"], entry["source"])
    info["source"] = entry["source"]
    info["seed_dir"] = str(entry["dir"])
    return info


def status_report(store_path, seed_dir, user_dir=None):
    """Return ``(status list, warnings)``; see ``status`` and ``collect``."""
    entries, warnings = collect(seed_dir, user_dir)
    return [_entry_status(store_path, entry) for entry in entries], warnings


def status(store_path, seed_dir, user_dir=None):
    """One entry per seed profile: its state in the store and, when outdated, its files.

    States: ``missing`` (not in the store yet), ``current``, ``outdated``
    (the seed's ``seed_version`` is higher), ``newer``, ``local`` (the store
    profile has no ``seed_version``), ``unreadable`` (broken front matter).
    File states of an outdated profile: ``same``, ``changed`` (with a unified
    ``diff`` from the store copy to the seed file), ``missing``. Each entry
    also names its ``source`` (``plugin`` or ``user``) and ``seed_dir``.
    """
    return status_report(store_path, seed_dir, user_dir)[0]


def _stored_approval(path):
    try:
        meta, _ = frontmatter.load(path)
    except CfpError:
        return False  # a broken file was never usable, so its replacement needs a fresh approval
    return bool(meta.get("approved", False))


def update(store_path, seed_dir, profile_id, files=None, all_files=False, user_dir=None):
    """Replace an outdated store profile with its seed (shipped or the user's own).

    ``profile.md`` is always replaced, because it carries the version. Other
    seed files that differ or are missing are taken only when named in
    ``files`` or with ``all_files``. Replaced profile and event files keep
    the approval flag of the store copy. Nothing is written when the call is
    refused.
    """
    profile_id = store.check_id(profile_id, "profile id")
    entries, warnings = collect(seed_dir, user_dir)
    entry = next((e for e in entries if e["name"] == profile_id), None)
    if entry is None:
        if user_dir is None:
            raise CfpError(f"no shipped profile '{profile_id}' in {seed_dir}")
        raise CfpError(f"no seed profile '{profile_id}' in {seed_dir} or {user_dir}")
    seed_profile_dir = entry["dir"]
    info = _profile_status(store_path, seed_profile_dir, entry["source"])
    if info["state"] != "outdated":
        raise CfpError(f"profile '{profile_id}' is not outdated (state: {info['state']}); nothing to update")

    states = {entry["path"]: entry["state"] for entry in info["files"]}
    open_files = [path for path, state in states.items() if path != PROFILE_FILE and state != "same"]
    if all_files:
        chosen = set(open_files)
    else:
        chosen = set()
        for rel in files or []:
            rel = str(rel).strip()
            if not rel or rel == PROFILE_FILE:
                continue
            if rel not in states:
                raise CfpError(
                    f"'{rel}' is not a file of the shipped profile '{profile_id}'; shipped files: {', '.join(states)}"
                )
            chosen.add(rel)

    target_dir = store.profile_dir(store_path, profile_id)
    writes = [PROFILE_FILE] + [path for path in open_files if path in chosen]
    linked = [
        str(path)
        for path in [target_dir] + [target_dir / sub for sub in SEED_SUBDIRS] + [target_dir / rel for rel in writes]
        if path.is_symlink()
    ]
    if linked:
        # frontmatter.save writes through a link, which would change a file outside the store.
        raise CfpError(
            f"profile '{profile_id}' in the store contains symlinks ({', '.join(linked)}); "
            "replace them with regular files before updating"
        )
    updated, added = [], []
    for rel in writes:
        meta, body = frontmatter.load(seed_profile_dir / rel)
        target = target_dir / rel
        existed = target.is_file()
        if existed and (rel == PROFILE_FILE or rel.startswith(APPROVED_PREFIXES)):
            meta["approved"] = _stored_approval(target)
        if rel == PROFILE_FILE:
            meta["seed_version"] = str(meta.get("seed_version") or "")
        frontmatter.save(target, meta, body)
        (updated if existed else added).append(rel)
    return {
        "profile": profile_id,
        "from_version": info["store_version"],
        "to_version": info["seed_version"],
        "updated": updated,
        "added": added,
        "skipped": [path for path in open_files if path not in chosen],
        "source": entry["source"],
        "warnings": warnings,
    }
