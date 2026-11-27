"""Proposal status transitions, side effects, and submission counting."""

from cfplib import CfpError, frontmatter, profile, proposals, store, talks, text as textutil

STATUSES = proposals.STATUS_ORDER  # one status tuple; proposals owns it because lifecycle imports proposals

# ready -> draft: the user reopens a ready proposal for edits (content edits do
# this automatically, see proposals.demote_ready). accepted -> withdrawn: the
# speaker cancels after acceptance.
TRANSITIONS = {
    "draft": ["ready", "submitted", "withdrawn"],
    "ready": ["draft", "submitted", "withdrawn"],
    "submitted": ["accepted", "rejected", "withdrawn"],
    "accepted": ["presented", "withdrawn"],
    "rejected": [],
    "withdrawn": [],
    "presented": [],
}

DATE_FIELDS = {
    "ready": "ready_on",
    "submitted": "submitted_on",
    "accepted": "decided_on",
    "rejected": "decided_on",
    "withdrawn": "decided_on",
    "presented": "presented_on",
}

COUNTED_STATUSES = {"submitted", "accepted", "rejected", "presented"}


def last_verdict(meta):
    rounds = meta.get("review_rounds") or []
    if not rounds:
        return None
    return (rounds[-1] or {}).get("verdict")


def ready_check(store_path, proposal_id):
    _, meta, _ = proposals.load_proposal(store_path, proposal_id)
    reasons = []
    verdict = last_verdict(meta)
    if verdict != "pass":
        if verdict is None:
            reasons.append("no committee review recorded yet; the last verdict must be pass")
        else:
            reasons.append(f"last committee review verdict is '{verdict}', must be pass")
    elif meta.get("review_stale"):
        reasons.append("the proposal was edited after the last passing review; run the committee review again")
    preflight = meta.get("preflight") or {}
    if not preflight:
        reasons.append("pre-flight check has not run yet")
    elif not preflight.get("ok"):
        reasons.append("pre-flight check reported disqualifying findings")
    return {"can_ready": not reasons, "reasons": reasons}


def count_submissions(store_path, event_id, exclude_proposal=None):
    """Return (count, problems) of proposals that count toward the event's limit.

    Proposals are counted once per id (a sync "conflicted copy" of a file does
    not count twice). ``problems`` lists proposal files that could not be
    parsed; those are not counted, so the caller can warn that the count may
    be low.
    """
    items, problems = store.list_dir(store_path, "proposals")
    counted = set()
    for path, meta, _ in items:
        proposal_id = meta.get("id") or path.stem
        if exclude_proposal and proposal_id == exclude_proposal:
            continue
        if meta.get("event") == event_id and meta.get("status") in COUNTED_STATUSES:
            counted.add(proposal_id)
    return len(counted), problems


def _event_year(store_path, meta, fallback_date):
    try:
        event = profile.load_event(store_path, meta.get("profile"), meta.get("event"))
    except CfpError:
        event = {}
    for key in ("event_start", "event_end"):
        parsed = textutil.parse_date(event.get(key))
        if parsed:
            return parsed.year
    parsed = textutil.parse_date(fallback_date)
    return parsed.year if parsed else None


def _add_accepted_example(store_path, meta, body, date):
    sections = frontmatter.sections(body)
    title = sections.get("Field: title", "")
    abstract = sections.get("Field: abstract", "")
    benefits = ""
    try:
        eff = profile.load_effective(store_path, meta.get("profile"), meta.get("event"))
        relevance_id = eff.get("relevance_field")
        if relevance_id:
            benefits = sections.get(f"Field: {relevance_id}", "")
    except CfpError:
        benefits = sections.get("Field: benefits", "")
    if not title:
        title = meta.get("id", "untitled")
    path = profile.add_example(
        store_path,
        meta["profile"],
        {
            "id": meta["id"],
            "title": title,
            "abstract": abstract,
            "benefits": benefits,
            "event": meta.get("event", ""),
            "year": _event_year(store_path, meta, date),
            "origin": "own-accepted",
            "proposal": meta["id"],
        },
        today=date,
    )
    return f"added calibration example {path}"


def _record_outing(store_path, meta, date):
    talk_id = meta.get("talk")
    try:
        path, talk_meta, talk_body = talks.load_talk(store_path, talk_id)
    except CfpError as error:
        raise CfpError(f"talk '{talk_id}' of proposal '{meta.get('id')}': {error}")
    outings = talk_meta.get("outings") or []
    if not isinstance(outings, list):
        outings = [outings]
    outing = {"event": meta.get("event", ""), "family": meta.get("profile", ""), "date": date, "link": "", "kind": "presented"}
    if outing not in outings:
        outings.append(outing)
    talk_meta["outings"] = outings
    talk_meta["updated"] = date
    store.save(path, talk_meta, talk_body)
    return f"recorded presented outing on talk {talk_id} ({meta.get('event')}, {date})"


def set_status(store_path, proposal_id, to, date=None, force=False, today=None):
    path, meta, body = proposals.load_proposal(store_path, proposal_id)
    if not meta.get("profile"):
        raise CfpError(f"proposal '{proposal_id}' has no 'profile' in its front matter")
    current = meta.get("status") or "draft"
    if to not in STATUSES:
        raise CfpError(f"unknown status '{to}'; valid statuses: {', '.join(STATUSES)}")
    allowed = TRANSITIONS.get(current, [])
    if to not in allowed:
        targets = ", ".join(allowed) if allowed else "none"
        raise CfpError(f"cannot move proposal '{proposal_id}' from {current} to {to}; allowed targets: {targets}")
    side_effects = []
    if to == "ready" and not force:
        check = ready_check(store_path, proposal_id)
        if not check["can_ready"]:
            raise CfpError(
                "proposal is not ready: " + "; ".join(check["reasons"]) + " (use --force to set ready manually)"
            )
    elif to == "ready" and force:
        side_effects.append("ready was forced without the review and pre-flight checks")

    today_value = textutil.today_iso(today)
    date_value = str(date) if date else today_value
    if textutil.parse_date(date_value) is None:
        raise CfpError(f"date must be ISO YYYY-MM-DD, got {date_value!r}")

    if to == "accepted":
        side_effects.append(_add_accepted_example(store_path, meta, body, date_value))
    elif to == "presented":
        side_effects.append(_record_outing(store_path, meta, date_value))

    meta["status"] = to
    if to == "draft":
        proposals.invalidate_checks(meta)
        side_effects.append("ready_on cleared and checks marked stale; run the review and pre-flight again before setting ready")
    else:
        meta[DATE_FIELDS[to]] = date_value
    meta["updated"] = today_value
    store.save(path, meta, body)
    return {"from": current, "to": to, "date": date_value, "side_effects": side_effects}
