"""Store paths, slugs, and generic file access."""

import os
import re
import unicodedata
from pathlib import Path

from cfplib import CfpError, frontmatter

SLUG_MAX = 60
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def slugify(text, existing=None):
    """Lowercase ASCII slug, hyphen separated, at most 60 characters.

    ``existing`` is a collection of taken slugs; collisions get ``-2``, ``-3``.
    """
    normalized = unicodedata.normalize("NFKD", str(text or ""))
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    if len(slug) > SLUG_MAX:
        slug = slug[:SLUG_MAX].rstrip("-")
    if not slug:
        slug = "item"
    if existing is None:
        return slug
    candidate = slug
    counter = 2
    while candidate in existing:
        suffix = f"-{counter}"
        candidate = slug[: SLUG_MAX - len(suffix)].rstrip("-") + suffix
        counter += 1
    return candidate


def case_alias(directory, name):
    """The entry of ``directory`` that differs from ``name`` only in case, else None.

    Profile names are case-insensitive on every file system (like
    ``existing_ids``): on APFS or NTFS both spellings are one folder, and on a
    case-sensitive file system two such profiles would behave differently per
    platform. None when the exact name exists or the folder cannot be listed.
    """
    try:
        names = os.listdir(directory)
    except OSError:
        return None
    if name in names:
        return None
    return next((entry for entry in names if entry.lower() == name.lower()), None)


def check_id(value, what="id"):
    value = str(value or "")
    if not _SAFE_ID.fullmatch(value) or ".." in value:
        raise CfpError(f"invalid {what}: {value!r} (use letters, digits, hyphens)")
    return value


# ---------------------------------------------------------------- paths


def talk_path(store, talk_id):
    return Path(store) / "talks" / f"{check_id(talk_id, 'talk id')}.md"


def proposal_path(store, proposal_id):
    return Path(store) / "proposals" / f"{check_id(proposal_id, 'proposal id')}.md"


def proposal_id(event_id, talk_id):
    return f"{event_id}--{talk_id}"


def bio_path(store, name):
    return Path(store) / "bios" / f"{check_id(name, 'bio name')}.md"


def resource_path(store, resource_id):
    return Path(store) / "resources" / f"{check_id(resource_id, 'resource id')}.md"


def profile_dir(store, profile_id):
    return Path(store) / "profiles" / check_id(profile_id, "profile id")


def profile_path(store, profile_id):
    return profile_dir(store, profile_id) / "profile.md"


def event_path(store, profile_id, event_id):
    return profile_dir(store, profile_id) / "events" / f"{check_id(event_id, 'event id')}.md"


def example_path(store, profile_id, example_id):
    return profile_dir(store, profile_id) / "examples" / f"{check_id(example_id, 'example id')}.md"


# ---------------------------------------------------------------- generic io


def exists(path):
    return Path(path).is_file()


def load(path):
    path = Path(path)
    if not path.is_file():
        raise CfpError(f"not found: {path}")
    return frontmatter.load(path)


def save(path, meta, body):
    return frontmatter.save(path, meta, body)


def list_dir(store, relative):
    """Return (items, problems) for every .md file in <store>/<relative>.

    items: list of (path, meta, body) sorted by file name.
    problems: list of {path, error} for files whose front matter did not parse.
    """
    parts = Path(relative).parts
    if Path(relative).is_absolute() or ".." in parts:
        raise CfpError(f"invalid store directory: {relative!r}")
    directory = Path(store) / relative
    items = []
    problems = []
    if not directory.is_dir():
        return items, problems
    for path in sorted(directory.glob("*.md")):
        try:
            meta, body = frontmatter.load(path)
        except CfpError as error:
            problems.append({"path": str(path), "error": str(error)})
            continue
        items.append((path, meta, body))
    return items, problems


def existing_ids(store, relative):
    """Lowercased stems of the .md files in <store>/<relative>, for slug collision checks.

    Lowercasing matters on case-insensitive file systems (APFS, NTFS), where a
    new slug ``foo`` would otherwise overwrite an existing ``Foo.md``.
    """
    directory = Path(store) / relative
    if not directory.is_dir():
        return set()
    return {p.stem.lower() for p in directory.glob("*.md")}


def list_profile_ids(store):
    directory = Path(store) / "profiles"
    if not directory.is_dir():
        return []
    # Hidden folders (for example a ``.<id>.seeding`` left by a killed init) are not profiles.
    return sorted(p.name for p in directory.iterdir() if not p.name.startswith(".") and (p / "profile.md").is_file())
