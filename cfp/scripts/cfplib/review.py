"""Committee review: packet for the reviewer agent, round recording, history."""

from cfplib import CfpError, bios, profile, proposals, talks, text as textutil

MAX_SUGGESTIONS = 5
VERDICTS = ("pass", "revise")


def _criteria(eff):
    criteria = (eff.get("rubric") or {}).get("criteria") or []
    if not criteria:
        raise CfpError("the profile's rubric has no criteria; the committee review cannot run")
    return criteria


def packet(store_path, proposal_id, examples=3):
    _, meta, body = proposals.load_proposal(store_path, proposal_id)
    eff = proposals.effective_for(store_path, meta)
    rubric = eff.get("rubric") or {}
    criteria = _criteria(eff)
    texts = proposals.field_texts(body)
    fields = []
    for field in eff.get("fields", []):
        field_id = str(field.get("id"))
        fields.append(
            {
                "id": field_id,
                "label": field.get("label", field_id),
                "kind": field.get("kind", "text"),
                "audience": field.get("audience", "public"),
                "required": bool(field.get("required", False)),
                "text": texts.get(field_id, ""),
            }
        )
    session_type = next((t for t in eff.get("session_types", []) if t.get("id") == meta.get("session_type")), None)
    try:
        talk = talks.show_talk(store_path, meta.get("talk"))
        talk_info = {
            "id": talk["id"],
            "title": talk.get("title", ""),
            "personas": talk.get("personas", []),
            "projects": talk.get("projects", []),
            "outings": talk.get("outings", []),
            "sections": talk.get("sections", {}),
        }
    except CfpError:
        talk_info = {"id": meta.get("talk"), "title": "", "personas": [], "projects": [], "outings": [], "sections": {}}
    resources = []
    for resource_id in meta.get("resources") or []:
        try:
            resource = bios.load_resource(store_path, resource_id)
        except CfpError:
            continue
        resources.append({"id": resource["id"], "type": resource["type"], "title": resource["title"], "link": resource["link"]})
    examples_found, _ = profile.list_examples(store_path, meta.get("profile"), limit=examples)
    example_list = [
        {k: e.get(k) for k in ("title", "abstract", "benefits", "event", "year", "origin")} for e in examples_found
    ]
    return {
        "packet": {
            "proposal": proposal_id,
            "profile": meta.get("profile"),
            "profile_name": (eff.get("profile") or {}).get("name", ""),
            "event": meta.get("event"),
            "event_name": (eff.get("event") or {}).get("name", ""),
            "round": len(meta.get("review_rounds") or []) + 1,
            "rubric": {"scale_max": rubric.get("scale_max", 5), "criteria": criteria},
            "thresholds": {
                "pass_average": rubric.get("pass_average", 4.0),
                "pass_min_criterion": rubric.get("pass_min_criterion", 3.0),
            },
            "rejection_reasons": list(eff.get("rejection_reasons") or []),
            "drafting_guidance": eff.get("drafting_guidance", ""),
            "examples": example_list,
            "session_type": session_type or {"id": meta.get("session_type")},
            "track": meta.get("track"),
            "audience_level": meta.get("audience_level"),
            "angle": meta.get("angle"),
            "fields": fields,
            "relevance_field": eff.get("relevance_field"),
            # A reviewer sees no bio when the form has none, so the packet carries none.
            "bio_on_form": bool(eff.get("bio_on_form", True)),
            "bio": proposals.bio_text(body) if eff.get("bio_on_form", True) else "",
            "resources": resources,
            "co_speakers": meta.get("co_speakers") or [],
            "talk": talk_info,
        }
    }


def _validate(data, criteria, scale_max):
    if not isinstance(data, dict):
        raise CfpError("reviewer JSON must be an object")
    scores = data.get("scores")
    comments = data.get("comments")
    if not isinstance(scores, dict):
        raise CfpError("reviewer JSON needs a 'scores' object with one number per criterion")
    if not isinstance(comments, dict):
        raise CfpError("reviewer JSON needs a 'comments' object with one comment per criterion")
    clean_scores = {}
    clean_comments = {}
    for criterion in criteria:
        cid = str(criterion.get("id"))
        if cid not in scores:
            raise CfpError(f"reviewer JSON is missing a score for criterion '{cid}'")
        value = scores[cid]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise CfpError(f"score for '{cid}' must be a number, got {value!r}")
        if value < 0 or value > scale_max:
            raise CfpError(f"score for '{cid}' must be between 0 and {scale_max}, got {value}")
        clean_scores[cid] = float(value)
        comment = comments.get(cid)
        if not isinstance(comment, str) or not comment.strip():
            raise CfpError(f"reviewer JSON is missing a comment for criterion '{cid}'")
        clean_comments[cid] = comment.strip()
    suggestions = data.get("suggestions") or []
    if not isinstance(suggestions, list):
        raise CfpError("'suggestions' must be a list of {field, text}")
    clean_suggestions = []
    for item in suggestions:
        if not isinstance(item, dict) or not item.get("field") or not item.get("text"):
            raise CfpError("every suggestion needs a 'field' and a 'text'")
        clean_suggestions.append({"field": str(item["field"]), "text": str(item["text"]).strip()})
    reviewer_verdict = str(data.get("verdict") or "").strip().lower()
    if reviewer_verdict not in VERDICTS:
        reviewer_verdict = "revise"
    return clean_scores, clean_comments, clean_suggestions[:MAX_SUGGESTIONS], reviewer_verdict


def record(store_path, proposal_id, data, today=None):
    path, meta, body = proposals.load_proposal(store_path, proposal_id)
    eff = proposals.effective_for(store_path, meta)
    rubric = eff.get("rubric") or {}
    criteria = _criteria(eff)
    scale_max = float(rubric.get("scale_max", 5))
    pass_average = float(rubric.get("pass_average", 4.0))
    pass_min = float(rubric.get("pass_min_criterion", 3.0))
    scores, comments, suggestions, reviewer_verdict = _validate(data, criteria, scale_max)
    average = round(sum(scores.values()) / len(scores), 2)
    below_min = [cid for cid, value in scores.items() if value < pass_min]
    verdict = "pass" if average >= pass_average and not below_min else "revise"
    rounds = list(meta.get("review_rounds") or [])
    round_number = len(rounds) + 1
    rounds.append(
        {
            "round": round_number,
            "date": textutil.today_iso(today),
            "scores": scores,
            "comments": comments,
            "verdict": verdict,
            "reviewer_verdict": reviewer_verdict,
            "average": average,
            "suggestions": suggestions,
        }
    )
    meta["review_rounds"] = rounds
    meta["review_stale"] = False
    proposals._save(path, meta, body, eff, today)
    return {
        "round": round_number,
        "verdict": verdict,
        "reviewer_verdict": reviewer_verdict,
        "average": average,
        "below_min": below_min,
        "thresholds": {"pass_average": pass_average, "pass_min_criterion": pass_min},
        "suggestions": suggestions,
    }


def history(store_path, proposal_id):
    _, meta, _ = proposals.load_proposal(store_path, proposal_id)
    return {"rounds": list(meta.get("review_rounds") or [])}
