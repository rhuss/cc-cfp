"""Conference profiles, event overrides, calibration examples."""

import copy

from cfplib import CfpError, frontmatter, store, text as textutil

FIELD_KINDS = {"text", "longtext", "choice", "multichoice", "boolean", "link", "resources"}
RULE_KINDS = {
    "submission_limit",
    "repeat_within_months",
    "track_in_event",
    "speaker_count",
    "all_men_panel",
    "multi_company_panel",
    "vendor_pitch",
    "custom",
}
LIMIT_STATUSES = {"unverified", "page", "screenshot"}
SEVERITIES = ("disqualify", "warn")  # single source of truth; preflight and the CLI import it
AUDIENCES = {"public", "reviewer"}

PROFILE_DEFAULTS = {
    "id": "",
    "name": "",
    "platform": "",
    "approved": False,
    "seed_version": "",
    "sources": [],
    "session_types": [],
    "submission_limit": None,
    "selection_limit": "",
    "fields": [],
    "rubric": {"scale_max": 5, "pass_average": 4.0, "pass_min_criterion": 3.0, "criteria": []},
    "rules": [],
    "rejection_reasons": [],
    "bio_on_form": True,
    "bio_limit": None,
    "bio_limit_status": "unverified",
}
EVENT_DEFAULTS = {
    "id": "",
    "profile": "",
    "name": "",
    "location": "",
    "event_start": None,
    "event_end": None,
    "cfp_open": None,
    "cfp_close": None,
    "cfp_close_timezone": "",
    "notification": None,
    "approved": False,
    "sources": [],
    "tracks": [],
    "submission_limit": None,
    "session_type_overrides": [],
    "field_overrides": [],
}
PROFILE_SECTIONS = ("Drafting guidance", "Notes")
# Reviewer-only longtext fields with their own drafting rule; never the relevance field.
RELEVANCE_EXCLUDED_IDS = ("previously_presented", "resources")


def relevance_field_id(fields):
    """Id of the reviewer-only relevance field (why the talk belongs on the schedule), or None.

    An older form's ``benefits`` field wins when the form has one. Otherwise it
    is the first field in form order with ``audience: reviewer`` and
    ``kind: longtext`` whose id has no drafting rule of its own
    (``previously_presented``, ``resources``). The draft skill, the committee
    review packet, and the accepted-example capture all use this one answer.
    """
    fields = [field for field in (fields or []) if isinstance(field, dict)]
    if any(field.get("id") == "benefits" for field in fields):
        return "benefits"
    for field in fields:
        if (
            field.get("audience") == "reviewer"
            and field.get("kind") == "longtext"
            and field.get("id") not in RELEVANCE_EXCLUDED_IDS
        ):
            return field.get("id")
    return None


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


# ---------------------------------------------------------------- loading


def load_profile(store_path, profile_id):
    path = store.profile_path(store_path, profile_id)
    if not path.is_file():
        raise CfpError(f"unknown profile '{profile_id}' (no {path})")
    meta, body = store.load(path)
    data = copy.deepcopy(PROFILE_DEFAULTS)
    data.update(meta)
    data["id"] = profile_id
    sections = frontmatter.sections(body)
    data["drafting_guidance"] = sections.get("Drafting guidance", "")
    data["notes"] = sections.get("Notes", "")
    for key in ("sources", "session_types", "fields", "rules", "rejection_reasons"):
        data[key] = _as_list(data.get(key))
    if not isinstance(data.get("rubric"), dict):
        data["rubric"] = copy.deepcopy(PROFILE_DEFAULTS["rubric"])
    data["rubric"].setdefault("criteria", [])
    data["rubric"]["criteria"] = _as_list(data["rubric"]["criteria"])
    return data


def load_event(store_path, profile_id, event_id):
    path = store.event_path(store_path, profile_id, event_id)
    if not path.is_file():
        raise CfpError(f"unknown event '{event_id}' for profile '{profile_id}' (no {path})")
    meta, body = store.load(path)
    data = copy.deepcopy(EVENT_DEFAULTS)
    data.update(meta)
    data["id"] = event_id
    data["notes"] = frontmatter.sections(body).get("Notes", "")
    for key in ("sources", "tracks", "session_type_overrides", "field_overrides"):
        data[key] = _as_list(data.get(key))
    return data


def _profile_subdir(store_path, profile_id, name):
    """Relative store path of a profile subdirectory, with the id validated."""
    return f"profiles/{store.check_id(profile_id, 'profile id')}/{name}"


def list_events(store_path, profile_id, today=None):
    items, problems = store.list_dir(store_path, _profile_subdir(store_path, profile_id, "events"))
    events = []
    for path, meta, _ in items:
        event_id = meta.get("id") or path.stem
        events.append(
            {
                "id": event_id,
                "name": meta.get("name", ""),
                "location": meta.get("location", ""),
                "cfp_open": meta.get("cfp_open"),
                "cfp_close": meta.get("cfp_close"),
                "event_start": meta.get("event_start"),
                "notification": meta.get("notification"),
                "approved": bool(meta.get("approved", False)),
                "tracks": len(_as_list(meta.get("tracks"))),
                "days_to_close": days_to_close(meta, today) if today else None,
            }
        )
    return events, problems


def list_profiles(store_path, today=None):
    profiles = []
    problems = []
    for profile_id in store.list_profile_ids(store_path):
        try:
            prof = load_profile(store_path, profile_id)
        except CfpError as error:
            problems.append({"path": str(store.profile_path(store_path, profile_id)), "error": str(error)})
            continue
        events, event_problems = list_events(store_path, profile_id, today)
        problems.extend(event_problems)
        profiles.append(
            {
                "id": profile_id,
                "name": prof.get("name", ""),
                "platform": prof.get("platform", ""),
                "approved": bool(prof.get("approved", False)),
                "seed_version": prof.get("seed_version", ""),
                "events": events,
            }
        )
    return profiles, problems


# ---------------------------------------------------------------- merge


def _merge_by_id(base_items, overrides, allow_remove):
    result = [copy.deepcopy(item) for item in base_items]
    index = {item.get("id"): pos for pos, item in enumerate(result)}
    for override in overrides:
        if not isinstance(override, dict) or not override.get("id"):
            continue
        item_id = override["id"]
        if allow_remove and override.get("remove"):
            if item_id in index:
                result[index[item_id]] = None
            continue
        patch = {k: v for k, v in override.items() if k != "remove"}
        if item_id in index and result[index[item_id]] is not None:
            result[index[item_id]].update(patch)
        else:
            result.append(patch)
            index[item_id] = len(result) - 1
    return [item for item in result if item is not None]


def effective(profile, event):
    """Merge an event override onto a family profile."""
    session_types = _merge_by_id(profile.get("session_types", []), (event or {}).get("session_type_overrides", []), True)
    fields = _merge_by_id(profile.get("fields", []), (event or {}).get("field_overrides", []), False)
    tracks = list((event or {}).get("tracks") or [])
    for field in fields:
        if field.get("id") == "track" and tracks:
            field["options"] = list(tracks)
        if "limit" in field:
            field["limit"] = textutil.coerce_limit(field.get("limit"))
    submission_limit = profile.get("submission_limit")
    if event and event.get("submission_limit") is not None:
        submission_limit = event["submission_limit"]
    approved = bool(profile.get("approved")) and (bool(event.get("approved")) if event else True)
    profile_info = {
        key: profile.get(key)
        for key in ("id", "name", "platform", "approved", "seed_version", "sources", "selection_limit")
    }
    event_info = None
    if event:
        event_info = {
            key: event.get(key)
            for key in (
                "id",
                "name",
                "location",
                "event_start",
                "event_end",
                "cfp_open",
                "cfp_close",
                "cfp_close_timezone",
                "notification",
                "approved",
                "sources",
                "submission_limit",
                "notes",
            )
        }
    return {
        "profile": profile_info,
        "event": event_info,
        "session_types": session_types,
        "fields": fields,
        "relevance_field": relevance_field_id(fields),
        "rubric": copy.deepcopy(profile.get("rubric") or {}),
        "rules": copy.deepcopy(profile.get("rules") or []),
        "rejection_reasons": list(profile.get("rejection_reasons") or []),
        "submission_limit": submission_limit,
        # Only an explicit false switches the bio off; an unusable value is a
        # validation problem and must not hide the bio by accident.
        "bio_on_form": profile.get("bio_on_form") is not False,
        "bio_limit": textutil.coerce_limit(profile.get("bio_limit")),
        "bio_limit_status": profile.get("bio_limit_status") or "unverified",
        "tracks": tracks,
        "approved": approved,
        "drafting_guidance": profile.get("drafting_guidance", ""),
        "notes": profile.get("notes", ""),
    }


def load_effective(store_path, profile_id, event_id=None):
    profile = load_profile(store_path, profile_id)
    event = load_event(store_path, profile_id, event_id) if event_id else None
    return effective(profile, event)


# ---------------------------------------------------------------- validation


def validate(store_path, profile_id, event_id=None):
    problems = []
    try:
        profile = load_profile(store_path, profile_id)
    except CfpError as error:
        return [str(error)]
    seen = set()
    for field in profile["fields"]:
        if not isinstance(field, dict) or not field.get("id"):
            problems.append("field without id")
            continue
        if field["id"] in seen:
            problems.append(f"duplicate field id '{field['id']}'")
        seen.add(field["id"])
        if field.get("kind") not in FIELD_KINDS:
            problems.append(f"field '{field['id']}': unknown kind {field.get('kind')!r}")
        if field.get("limit_status", "unverified") not in LIMIT_STATUSES:
            problems.append(f"field '{field['id']}': unknown limit_status {field.get('limit_status')!r}")
        if field.get("audience", "public") not in AUDIENCES:
            problems.append(f"field '{field['id']}': unknown audience {field.get('audience')!r}")
        limit = field.get("limit")
        if limit is not None and (not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0):
            problems.append(f"field '{field['id']}': limit must be a positive integer or empty")
    seen = set()
    for session_type in profile["session_types"]:
        if not isinstance(session_type, dict) or not session_type.get("id"):
            problems.append("session type without id")
            continue
        if session_type["id"] in seen:
            problems.append(f"duplicate session type id '{session_type['id']}'")
        seen.add(session_type["id"])
    seen = set()
    for rule in profile["rules"]:
        if not isinstance(rule, dict) or not rule.get("id"):
            problems.append("rule without id")
            continue
        if rule["id"] in seen:
            problems.append(f"duplicate rule id '{rule['id']}'")
        seen.add(rule["id"])
        if rule.get("kind") not in RULE_KINDS:
            problems.append(f"rule '{rule['id']}': unknown rule kind {rule.get('kind')!r}")
        if rule.get("severity", "disqualify") not in SEVERITIES:
            problems.append(f"rule '{rule['id']}': unknown severity {rule.get('severity')!r}")
    rubric = profile["rubric"]
    criteria = rubric.get("criteria") or []
    if profile.get("approved") and not criteria:
        problems.append("rubric has no criteria but the profile is approved")
    seen = set()
    for criterion in criteria:
        if not isinstance(criterion, dict) or not criterion.get("id"):
            problems.append("rubric criterion without id")
            continue
        if criterion["id"] in seen:
            problems.append(f"duplicate rubric criterion id '{criterion['id']}'")
        seen.add(criterion["id"])
    if profile.get("bio_limit_status", "unverified") not in LIMIT_STATUSES:
        problems.append(f"unknown bio_limit_status {profile.get('bio_limit_status')!r}")
    if not isinstance(profile.get("bio_on_form", True), bool):
        problems.append(f"bio_on_form must be true or false, got {profile.get('bio_on_form')!r}")

    if event_id:
        try:
            event = load_event(store_path, profile_id, event_id)
        except CfpError as error:
            return problems + [str(error)]
        if event.get("profile") and event["profile"] != profile_id:
            problems.append(f"event '{event_id}': profile is '{event['profile']}', expected '{profile_id}'")
        if not event.get("tracks"):
            problems.append(f"event '{event_id}': tracks list is empty, track checks cannot run")
        known_types = {t.get("id") for t in profile["session_types"] if isinstance(t, dict)}
        for override in event.get("session_type_overrides", []):
            if not isinstance(override, dict) or not override.get("id"):
                problems.append(f"event '{event_id}': session type override without id")
            elif override.get("remove") and override["id"] not in known_types:
                problems.append(f"event '{event_id}': removes unknown session type '{override['id']}'")
        for override in event.get("field_overrides", []):
            if not isinstance(override, dict) or not override.get("id"):
                problems.append(f"event '{event_id}': field override without id")
        for key in ("cfp_open", "cfp_close", "event_start", "event_end", "notification"):
            value = event.get(key)
            if value is not None and textutil.parse_date(value) is None:
                problems.append(f"event '{event_id}': {key} is not an ISO date: {value!r}")
    return problems


# ---------------------------------------------------------------- approval


def approve(store_path, profile_id, event_id=None, approved=True):
    if event_id:
        path = store.event_path(store_path, profile_id, event_id)
        if not path.is_file():
            raise CfpError(f"unknown event '{event_id}' for profile '{profile_id}'")
    else:
        path = store.profile_path(store_path, profile_id)
        if not path.is_file():
            raise CfpError(f"unknown profile '{profile_id}'")
    meta, body = store.load(path)
    meta["approved"] = bool(approved)
    store.save(path, meta, body)
    return {"path": str(path), "approved": bool(approved)}


def is_approved(store_path, profile_id, event_id=None):
    reasons = []
    profile = load_profile(store_path, profile_id)
    if not profile.get("approved"):
        reasons.append(f"profile '{profile_id}' is not approved (run /cfp:profile to review and approve it)")
    if event_id:
        event = load_event(store_path, profile_id, event_id)
        if not event.get("approved"):
            reasons.append(f"event override '{event_id}' is not approved")
    return (not reasons), reasons


# ---------------------------------------------------------------- writing


def write_profile_from_json(store_path, profile_id, data):
    path = store.profile_path(store_path, profile_id)
    if path.is_file():
        meta, body = store.load(path)
    else:
        meta, body = copy.deepcopy(PROFILE_DEFAULTS), ""
    data = dict(data or {})
    body_sections = data.pop("body", None) or {}
    for key in ("drafting_guidance", "notes"):
        value = data.pop(key, None)
        if value is not None:
            heading = "Drafting guidance" if key == "drafting_guidance" else "Notes"
            body_sections.setdefault(heading, value)
    meta.update(data)
    meta["id"] = profile_id
    meta["approved"] = bool(meta.get("approved", False))
    for heading, text in body_sections.items():
        body = frontmatter.set_section(body, heading, text)
    for heading in PROFILE_SECTIONS:
        if heading not in frontmatter.sections(body):
            body = frontmatter.set_section(body, heading, "")
    store.save(path, meta, body)
    return path


def write_event_from_json(store_path, profile_id, event_id, data):
    if not store.profile_path(store_path, profile_id).is_file():
        raise CfpError(f"unknown profile '{profile_id}'")
    path = store.event_path(store_path, profile_id, event_id)
    if path.is_file():
        meta, body = store.load(path)
    else:
        meta, body = copy.deepcopy(EVENT_DEFAULTS), ""
    data = dict(data or {})
    body_sections = data.pop("body", None) or {}
    notes = data.pop("notes", None)
    if notes is not None:
        body_sections.setdefault("Notes", notes)
    meta.update(data)
    meta["id"] = event_id
    meta["profile"] = profile_id
    # Approval always comes from the JSON (default false), so a rewritten
    # override must be reviewed again before drafting can use it.
    meta["approved"] = bool(data.get("approved", False))
    for heading, text in body_sections.items():
        body = frontmatter.set_section(body, heading, text)
    if "Notes" not in frontmatter.sections(body):
        body = frontmatter.set_section(body, "Notes", "")
    store.save(path, meta, body)
    return path


# ---------------------------------------------------------------- examples


def add_example(store_path, profile_id, data, today=None):
    if not store.profile_path(store_path, profile_id).is_file():
        raise CfpError(f"unknown profile '{profile_id}'")
    title = str(data.get("title") or "").strip()
    if not title:
        raise CfpError("example needs a title")
    existing = store.existing_ids(store_path, _profile_subdir(store_path, profile_id, "examples"))
    example_id = data.get("id") or data.get("proposal") or store.slugify(title)
    if str(example_id).lower() in existing and not data.get("id"):
        example_id = store.slugify(example_id, existing)
    meta = {
        "id": example_id,
        "profile": profile_id,
        "event": data.get("event", ""),
        "year": data.get("year"),
        "origin": data.get("origin", "manual"),
        "proposal": data.get("proposal") or None,
        "added": textutil.today_iso(today),
    }
    body = ""
    body = frontmatter.set_section(body, "Title", title)
    body = frontmatter.set_section(body, "Abstract", str(data.get("abstract") or ""))
    body = frontmatter.set_section(body, "Benefits", str(data.get("benefits") or ""))
    if data.get("why"):
        body = frontmatter.set_section(body, "Why it worked", str(data["why"]))
    path = store.example_path(store_path, profile_id, example_id)
    store.save(path, meta, body)
    return path


def list_examples(store_path, profile_id, limit=None):
    """Return (examples newest first, problems), like every other list function."""
    items, problems = store.list_dir(store_path, _profile_subdir(store_path, profile_id, "examples"))
    examples = []
    for path, meta, body in items:
        sections = frontmatter.sections(body)
        examples.append(
            {
                "id": meta.get("id") or path.stem,
                "event": meta.get("event", ""),
                "year": meta.get("year"),
                "origin": meta.get("origin", ""),
                "proposal": meta.get("proposal") or "",
                "added": str(meta.get("added") or ""),
                "title": sections.get("Title", ""),
                "abstract": sections.get("Abstract", ""),
                "benefits": sections.get("Benefits", ""),
                "why": sections.get("Why it worked", ""),
            }
        )
    examples.sort(key=lambda e: (e["added"], str(e["year"] or "")), reverse=True)
    if limit is not None:
        examples = examples[: max(int(limit), 0)]
    return examples, problems


# ---------------------------------------------------------------- dates


def days_to_close(event, today):
    close = textutil.parse_date((event or {}).get("cfp_close"))
    today_date = textutil.parse_date(today) or textutil.parse_date(textutil.today_iso())
    if close is None:
        return None
    return (close - today_date).days
