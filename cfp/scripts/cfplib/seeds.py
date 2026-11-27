"""Shipped seed profiles: compare them with the store copies and update outdated ones.

``config init`` copies a seed profile into a store once and never touches it
again. A later plugin version can ship a newer seed, marked by a higher
``seed_version`` in its ``profile.md``. ``status`` reports that with a diff
per shipped file, and ``update`` replaces the files the user chose while
keeping their approval flags. Files that exist only in the store (the user's
own events, examples of accepted proposals) are never read or written here.
"""

import difflib
from pathlib import Path

from cfplib import CfpError, frontmatter, store

PROFILE_FILE = "profile.md"
SEED_SUBDIRS = ("events", "examples")
# Besides profile.md, files under these directories carry an approval flag.
APPROVED_PREFIXES = ("events/",)


def _seed_profiles(seed_dir):
    seed_dir = Path(seed_dir)
    if not seed_dir.is_dir():
        raise CfpError(f"seed directory not found: {seed_dir}")
    return [entry for entry in sorted(seed_dir.iterdir()) if entry.is_dir() and (entry / PROFILE_FILE).is_file()]


def _seed_files(seed_profile_dir):
    """Relative paths of the files a seed ships: profile.md, events/*.md, examples/*.md.

    Symlinks are skipped, as in the initial copy, so a stray link in a seed
    directory cannot pull foreign files into the store.
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


def _diff(store_text, seed_text, rel):
    lines = difflib.unified_diff(
        store_text.splitlines(),
        seed_text.splitlines(),
        fromfile=f"store/{rel}",
        tofile=f"shipped/{rel}",
        lineterm="",
        n=2,
    )
    return "\n".join(lines)


def _file_states(seed_profile_dir, target_dir):
    files = []
    for rel in _seed_files(seed_profile_dir):
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
            files.append({"path": rel, "state": "changed", "diff": _diff(store_text, seed_text, rel)})
    return files


def _profile_status(store_path, seed_profile_dir):
    profile_id = seed_profile_dir.name
    seed_meta, _ = frontmatter.load(seed_profile_dir / PROFILE_FILE)
    seed_version = str(seed_meta.get("seed_version") or "")
    info = {"profile": profile_id, "state": "", "store_version": None, "seed_version": seed_version, "files": []}
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
        info["files"] = _file_states(seed_profile_dir, target_dir)
    else:
        info["state"] = "newer"  # the store was seeded by a later plugin version
    return info


def status(store_path, seed_dir):
    """One entry per shipped seed profile: its state in the store and, when outdated, its files.

    States: ``missing`` (not in the store yet), ``current``, ``outdated``
    (the shipped ``seed_version`` is higher), ``newer``, ``local`` (the store
    profile has no ``seed_version``), ``unreadable`` (broken front matter).
    File states of an outdated profile: ``same``, ``changed`` (with a unified
    ``diff`` from the store copy to the shipped file), ``missing``.
    """
    return [_profile_status(store_path, entry) for entry in _seed_profiles(seed_dir)]


def _stored_approval(path):
    try:
        meta, _ = frontmatter.load(path)
    except CfpError:
        return False  # a broken file was never usable, so its replacement needs a fresh approval
    return bool(meta.get("approved", False))


def update(store_path, seed_dir, profile_id, files=None, all_files=False):
    """Replace an outdated store profile with the shipped seed.

    ``profile.md`` is always replaced, because it carries the version. Other
    shipped files that differ or are missing are taken only when named in
    ``files`` or with ``all_files``. Replaced profile and event files keep
    the approval flag of the store copy. Nothing is written when the call is
    refused.
    """
    profile_id = store.check_id(profile_id, "profile id")
    if not Path(seed_dir).is_dir():
        raise CfpError(f"seed directory not found: {seed_dir}")
    seed_profile_dir = Path(seed_dir) / profile_id
    if not (seed_profile_dir / PROFILE_FILE).is_file():
        raise CfpError(f"no shipped profile '{profile_id}' in {seed_dir}")
    info = _profile_status(store_path, seed_profile_dir)
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
    updated, added = [], []
    for rel in [PROFILE_FILE] + [path for path in open_files if path in chosen]:
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
    }
