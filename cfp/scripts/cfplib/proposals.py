"""Proposal operations: create, show, list, field and meta updates, bio snapshot."""

import copy

from cfplib import CfpError, bios, frontmatter, profile, store, talks, text as textutil

STATUS_ORDER = ("draft", "ready", "submitted", "accepted", "presented", "rejected", "withdrawn")
FIELD_PREFIX = "Field: "
BIO_SECTION = "Bio"
META_SYNCED_FIELDS = ("track", "audience_level")
LENIENT_FIELDS = ("track",)
PROPOSAL_DEFAULTS = {
    "id": "",
    "talk": "",
    "profile": "",
    "event": "",
    "session_type": "",
    "track": None,
    "audience_level": None,
    "angle": None,
    "status": "draft",
    "created": None,
    "updated": None,
    "submitted_on": None,
    "decided_on": None,
    "presented_on": None,
    "ready_on": None,
    "bio_variation": None,
    "resources": [],
    "co_speakers": [],
    "co_speaker_genders": [],
    "voice_pass": False,
    "review_rounds": [],
    "review_stale": False,
    "preflight": {},
}


# ---------------------------------------------------------------- loading


def load_proposal(store_path, proposal_id):
    path = store.proposal_path(store_path, proposal_id)
    if not path.is_file():
        raise CfpError(f"unknown proposal '{proposal_id}'")
    meta, body = store.load(path)
    merged = copy.deepcopy(PROPOSAL_DEFAULTS)
    merged.update(meta)
    merged["id"] = proposal_id
    for key in ("resources", "co_speakers", "co_speaker_genders", "review_rounds"):
        if not isinstance(merged.get(key), list):
            merged[key] = [] if merged.get(key) in (None, "") else [merged[key]]
    if not isinstance(merged.get("preflight"), dict):
        merged["preflight"] = {}
    return path, merged, body


def effective_for(store_path, meta):
    return profile.load_effective(store_path, meta.get("profile"), meta.get("event"))


def field_texts(body):
    return {
        heading[len(FIELD_PREFIX):]: text
        for heading, text in frontmatter.sections(body).items()
        if heading.startswith(FIELD_PREFIX)
    }


def bio_text(body):
    return frontmatter.sections(body).get(BIO_SECTION, "")


def _save(path, meta, body, eff, today):
    meta["updated"] = textutil.today_iso(today)
    store.save(path, meta, _ordered_body(body, eff))


def invalidate_checks(meta):
    """Mark the stored review and pre-flight results as stale after an edit.

    The review history stays; ``review_stale`` tells ``ready_check`` that the
    last verdict predates the current text, and the pre-flight map is cleared
    so it has to run again.
    """
    meta["status"] = "draft"
    meta["ready_on"] = None
    meta["preflight"] = {}
    if meta.get("review_rounds"):
        meta["review_stale"] = True


def demote_ready(meta):
    """Content edits invalidate a ready proposal: back to draft with stale checks.

    FR-031a ties ``ready`` to a passing review and a clean pre-flight of the
    text that was reviewed. Only ``ready`` proposals are demoted on purpose:
    a draft with a passing review is edited legitimately by the voice pass
    and the over-limit shortening (FR-021, FR-022), which must not trigger a
    second review. Returns True when the status changed.
    """
    if meta.get("status") != "ready":
        return False
    invalidate_checks(meta)
    return True


def _with_demotion(result, demoted):
    if demoted:
        result["reset_to_draft"] = True
    return result


def _ordered_body(body, eff):
    """Field sections in effective form order, then Bio, then anything else."""
    sections = frontmatter.sections(body)
    ordered = {}
    for field in eff.get("fields", []):
        heading = FIELD_PREFIX + str(field.get("id"))
        if heading in sections:
            ordered[heading] = sections[heading]
    for heading, text in sections.items():
        if heading.startswith(FIELD_PREFIX) and heading not in ordered:
            ordered[heading] = text
    if BIO_SECTION in sections:
        ordered[BIO_SECTION] = sections[BIO_SECTION]
    for heading, text in sections.items():
        if heading not in ordered:
            ordered[heading] = text
    return frontmatter.build_body(frontmatter.preamble(body), ordered)


# ---------------------------------------------------------------- create, show, list


def _find_session_type(eff, session_type):
    for item in eff.get("session_types", []):
        if item.get("id") == session_type:
            return item
    known = ", ".join(str(t.get("id")) for t in eff.get("session_types", []))
    raise CfpError(f"unknown session type '{session_type}' for this event; known: {known}")


def create(store_path, talk_id, profile_id, event_id, session_type, angle=None, today=None):
    talks.load_talk(store_path, talk_id)
    approved, reasons = profile.is_approved(store_path, profile_id, event_id)
    if not approved:
        raise CfpError("; ".join(reasons))
    eff = profile.load_effective(store_path, profile_id, event_id)
    _find_session_type(eff, session_type)
    proposal_id = store.proposal_id(event_id, talk_id)
    path = store.proposal_path(store_path, proposal_id)
    if path.is_file():
        raise CfpError(f"proposal '{proposal_id}' already exists for talk '{talk_id}' and event '{event_id}' (resume it with --proposal)")
    today_value = textutil.today_iso(today)
    meta = copy.deepcopy(PROPOSAL_DEFAULTS)
    meta.update(
        {
            "id": proposal_id,
            "talk": talk_id,
            "profile": profile_id,
            "event": event_id,
            "session_type": session_type,
            "angle": angle,
            "created": today_value,
            "updated": today_value,
        }
    )
    store.save(path, meta, "")
    return {"path": str(path), "id": proposal_id}


def show(store_path, proposal_id):
    _, meta, body = load_proposal(store_path, proposal_id)
    result = dict(meta)
    result["fields"] = field_texts(body)
    result["bio"] = bio_text(body)
    return result


def list_proposals(store_path, status=None, event=None, talk=None):
    items, problems = store.list_dir(store_path, "proposals")
    listing = []
    for path, meta, body in items:
        proposal_status = meta.get("status") or "draft"
        if status and proposal_status != status:
            continue
        if event and meta.get("event") != event:
            continue
        if talk and meta.get("talk") != talk:
            continue
        listing.append(
            {
                "id": meta.get("id") or path.stem,
                "talk": meta.get("talk", ""),
                "title": field_texts(body).get("title", ""),
                "profile": meta.get("profile", ""),
                "event": meta.get("event", ""),
                "session_type": meta.get("session_type", ""),
                "status": proposal_status,
                "updated": meta.get("updated"),
                "submitted_on": meta.get("submitted_on"),
                "decided_on": meta.get("decided_on"),
                "presented_on": meta.get("presented_on"),
                "ready_on": meta.get("ready_on"),
            }
        )
    order = {name: pos for pos, name in enumerate(STATUS_ORDER)}
    listing.sort(key=lambda p: (order.get(p["status"], len(order)), str(p["updated"] or ""), p["id"]))
    return listing, problems


# ---------------------------------------------------------------- fields


def _find_field(eff, field_id):
    """The effective field definition with this id, or None when the form has no such field."""
    for field in eff.get("fields", []):
        if field.get("id") == field_id:
            return field
    return None


def _field_def(eff, field_id):
    field = _find_field(eff, field_id)
    if field is None:
        known = ", ".join(str(f.get("id")) for f in eff.get("fields", []))
        raise CfpError(f"unknown field '{field_id}' for this event; known fields: {known}")
    return field


def _canonical_choice(field, text):
    options = [str(o) for o in (field.get("options") or [])]
    kind = field.get("kind")
    value = textutil.normalize(text)
    if kind == "boolean":
        lowered = value.lower()
        if lowered in ("yes", "true", "y", "1"):
            return "Yes"
        if lowered in ("no", "false", "n", "0"):
            return "No"
        raise CfpError(f"field '{field['id']}' is a yes/no field, got {value!r}")
    if kind in ("choice", "multichoice") and options:
        lowered = {o.lower(): o for o in options}
        parts = [value] if kind == "choice" else [p.strip() for p in value.split(",") if p.strip()]
        chosen = []
        for part in parts:
            if part.lower() in lowered:
                chosen.append(lowered[part.lower()])
            elif field["id"] in LENIENT_FIELDS:
                # Track membership is a pre-flight rule (FR-028), not a write-time refusal,
                # so a value outside the event list is stored as typed and flagged later.
                chosen.append(part)
            else:
                raise CfpError(f"field '{field['id']}' must be one of: {', '.join(options)} (got {part!r})")
        return ", ".join(chosen) if kind == "multichoice" else chosen[0]
    return value


def field_result(field, text):
    """Count `text` against the field's limit; shared by set-field and count."""
    result = {"field": field["id"]}
    result.update(textutil.limit_result(textutil.count_chars(text), field.get("limit"), field.get("limit_status", "unverified")))
    return result


def set_field(store_path, proposal_id, field_id, text, today=None):
    path, meta, body = load_proposal(store_path, proposal_id)
    eff = effective_for(store_path, meta)
    field = _field_def(eff, field_id)
    value = _canonical_choice(field, text)
    body = frontmatter.set_section(body, FIELD_PREFIX + field_id, value)
    if field_id in META_SYNCED_FIELDS:
        meta[field_id] = value
    demoted = demote_ready(meta)
    _save(path, meta, body, eff, today)
    return _with_demotion(field_result(field, value), demoted)


def bio_result(eff, text):
    """Count a bio snapshot against the profile's bio limit; shared by set-bio-text and count.

    ``on_form`` is false when the profile says the form has no speaker bio
    (``bio_on_form: false``). A stored snapshot is still counted then, but it
    has no limit and the status is ``not-on-form``.
    """
    chars = textutil.count_chars(text)
    if not eff.get("bio_on_form", True):
        return {"chars": chars, "limit": None, "limit_status": None, "status": "not-on-form", "on_form": False}
    result = textutil.limit_result(chars, eff.get("bio_limit"), eff.get("bio_limit_status", "unverified"))
    result["on_form"] = True
    return result


def set_bio_text(store_path, proposal_id, text, today=None):
    path, meta, body = load_proposal(store_path, proposal_id)
    eff = effective_for(store_path, meta)
    value = textutil.normalize(text)
    body = frontmatter.set_section(body, BIO_SECTION, value)
    demoted = demote_ready(meta)
    _save(path, meta, body, eff, today)
    return _with_demotion(bio_result(eff, value), demoted)


def _resources_text(store_path, resource_ids):
    lines = []
    for resource_id in resource_ids:
        resource = bios.load_resource(store_path, resource_id)
        lines.append(f"{resource['title']}: {resource['link']}")
    return "\n".join(lines)


def set_meta(
    store_path,
    proposal_id,
    track=None,
    audience_level=None,
    bio=None,
    resources=None,
    co_speakers=None,
    co_speaker_genders=None,
    angle=None,
    session_type=None,
    today=None,
):
    path, meta, body = load_proposal(store_path, proposal_id)
    eff = effective_for(store_path, meta)
    updated = []

    def set_choice(field_id, value):
        nonlocal body
        field = _find_field(eff, field_id)
        if field is not None:
            value = _canonical_choice(field, value)
            body = frontmatter.set_section(body, FIELD_PREFIX + field_id, value)
        else:
            value = textutil.normalize(value)
        meta[field_id] = value
        updated.append(field_id)

    if session_type is not None:
        _find_session_type(eff, session_type)
        meta["session_type"] = session_type
        updated.append("session_type")
    if track is not None:
        set_choice("track", track)
    if audience_level is not None:
        set_choice("audience_level", audience_level)
    if angle is not None:
        meta["angle"] = textutil.normalize(angle)
        updated.append("angle")
    if bio is not None:
        shown = bios.show_bio(store_path, bio)
        meta["bio_variation"] = bio
        body = frontmatter.set_section(body, BIO_SECTION, shown["text"])
        updated.extend(["bio_variation", "bio"])
    if resources is not None:
        ids = [str(r).strip() for r in resources if str(r).strip()]
        text = _resources_text(store_path, ids)
        meta["resources"] = ids
        updated.append("resources")
        if _find_field(eff, "resources") is not None:
            body = frontmatter.set_section(body, FIELD_PREFIX + "resources", text)
    if co_speakers is not None:
        if not isinstance(co_speakers, list):
            raise CfpError("co_speakers must be a JSON list of strings like \"Name, Company\"")
        meta["co_speakers"] = [str(c) for c in co_speakers]
        updated.append("co_speakers")
    if co_speaker_genders is not None:
        if not isinstance(co_speaker_genders, list):
            raise CfpError("co_speaker_genders must be a JSON list of strings")
        meta["co_speaker_genders"] = [str(g) for g in co_speaker_genders]
        updated.append("co_speaker_genders")

    demoted = demote_ready(meta) if updated else False
    _save(path, meta, body, eff, today)
    return _with_demotion({"updated": updated}, demoted)


def mark_voice_pass(store_path, proposal_id, today=None):
    path, meta, body = load_proposal(store_path, proposal_id)
    eff = effective_for(store_path, meta)
    meta["voice_pass"] = True
    _save(path, meta, body, eff, today)
    return {"voice_pass": True}
