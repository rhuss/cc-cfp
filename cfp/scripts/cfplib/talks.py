"""Talk operations: write, show, list, completeness."""

from cfplib import CfpError, frontmatter, store, text as textutil

STORY_SECTIONS = ("Problem", "Contribution", "Takeaways", "What is new", "Story notes")
LIST_KEYS = ("personas", "projects", "resources", "outings", "source_material")
TALK_DEFAULTS = {
    "id": "",
    "title": "",
    "status": "active",
    "created": None,
    "updated": None,
    "personas": [],
    "projects": [],
    "resources": [],
    "outings": [],
    "source_material": [],
}


def load_talk(store_path, talk_id):
    path = store.talk_path(store_path, talk_id)
    if not path.is_file():
        raise CfpError(f"unknown talk '{talk_id}'")
    meta, body = store.load(path)
    return path, meta, body


def write_talk(store_path, talk_id, data, today=None):
    data = dict(data or {})
    sections_in = data.pop("sections", None) or {}
    for heading in sections_in:
        if heading not in STORY_SECTIONS:
            raise CfpError(f"unknown talk section '{heading}'; valid sections: {', '.join(STORY_SECTIONS)}")
    today_value = textutil.today_iso(today)

    if not talk_id and data.get("id"):
        talk_id = str(data["id"])
    if talk_id:
        store.check_id(talk_id, "talk id")
        path = store.talk_path(store_path, talk_id)
        created = not path.is_file()
    else:
        title = str(data.get("title") or "").strip()
        if not title:
            raise CfpError("a new talk needs a title")
        talk_id = store.slugify(title, store.existing_ids(store_path, "talks"))
        path = store.talk_path(store_path, talk_id)
        if path.exists():
            raise CfpError(f"talk file {path} already exists; pass --talk {talk_id} to update it")
        created = True

    if created:
        if not str(data.get("title") or "").strip():
            raise CfpError("a new talk needs a title")
        meta = dict(TALK_DEFAULTS)
        meta["created"] = today_value
        body = ""
    else:
        meta, body = store.load(path)

    for key, value in data.items():
        if key in ("id", "created"):
            continue
        meta[key] = value
    meta["id"] = talk_id
    for key in LIST_KEYS:
        if not isinstance(meta.get(key), list):
            meta[key] = [] if meta.get(key) in (None, "") else [meta[key]]
    _validate_outings(meta["outings"])
    meta["updated"] = today_value

    current = frontmatter.sections(body)
    ordered = {}
    for heading in STORY_SECTIONS:
        if heading in sections_in:
            ordered[heading] = textutil.normalize(sections_in[heading])
        else:
            ordered[heading] = current.get(heading, "")
    for heading, text in current.items():
        if heading not in ordered:
            ordered[heading] = text
    body = frontmatter.build_body(frontmatter.preamble(body), ordered)
    store.save(path, meta, body)
    return {"path": str(path), "id": talk_id, "created": created}


def _validate_outings(outings):
    """Reject outings whose date is not an ISO date (YYYY-MM-DD).

    The repeat rule in pre-flight skips outings it cannot date, so an
    unparseable date would silently disable the rule for that outing.
    Catching it at write time keeps the stored data trustworthy.
    """
    for index, outing in enumerate(outings, start=1):
        if not isinstance(outing, dict):
            raise CfpError(f"outing {index} must be a map with event, date, kind")
        raw = outing.get("date")
        if raw in (None, ""):
            continue
        if textutil.parse_date(raw) is None:
            raise CfpError(
                f"outing {index} ({outing.get('event') or 'unnamed event'}) has an invalid date '{raw}'; use YYYY-MM-DD"
            )


def show_talk(store_path, talk_id):
    _, meta, body = load_talk(store_path, talk_id)
    result = dict(TALK_DEFAULTS)
    result.update(meta)
    result["id"] = talk_id
    sections = frontmatter.sections(body)
    result["sections"] = {heading: sections.get(heading, "") for heading in STORY_SECTIONS}
    for heading, text in sections.items():
        result["sections"].setdefault(heading, text)
    return result


def complete_talk(store_path, talk_id):
    shown = show_talk(store_path, talk_id)
    missing = [heading for heading in STORY_SECTIONS if not shown["sections"].get(heading, "").strip()]
    missing_meta = [] if shown.get("personas") else ["personas"]
    return {"complete": not missing and not missing_meta, "missing": missing, "missing_meta": missing_meta}


def _last_presented(meta):
    dates = []
    for outing in meta.get("outings") or []:
        if isinstance(outing, dict) and outing.get("kind", "presented") == "presented" and outing.get("date"):
            dates.append(str(outing["date"]))
    return max(dates) if dates else None


def list_talks(store_path, status=None):
    items, problems = store.list_dir(store_path, "talks")
    proposal_items, proposal_problems = store.list_dir(store_path, "proposals")
    problems = problems + proposal_problems
    by_talk = {}
    for path, meta, _ in proposal_items:
        by_talk.setdefault(meta.get("talk"), []).append(meta.get("id") or path.stem)
    listing = []
    for path, meta, _ in items:
        talk_id = meta.get("id") or path.stem
        talk_status = meta.get("status") or "active"
        if status and talk_status != status:
            continue
        listing.append(
            {
                "id": talk_id,
                "title": meta.get("title", ""),
                "status": talk_status,
                "updated": meta.get("updated"),
                "proposals": sorted(by_talk.get(talk_id, [])),
                "last_presented": _last_presented(meta),
            }
        )
    return listing, problems
