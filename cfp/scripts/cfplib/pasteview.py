"""Paste view: every field in form order with text, counts, and flags."""

from cfplib import CfpError, counts, proposals

FORMATS = ("markdown", "json")


def _flags(info):
    flags = []
    if not info["drafted"]:
        flags.append("not drafted")
    if info["status"] == "over":
        flags.append("OVER LIMIT")
    if info["limit"] is not None and info["limit_status"] == "unverified":
        flags.append("limit unverified")
    return flags


def _count_label(info):
    if info["limit"] is None:
        return f"{info['chars']} chars (no limit)"
    label = f"{info['chars']}/{info['limit']} chars"
    if info["limit_status"] == "unverified":
        label += " (limit approximate, unverified)"
    return label


def build(store_path, proposal_id):
    _, meta, body = proposals.load_proposal(store_path, proposal_id)
    eff = proposals.effective_for(store_path, meta)
    counted = counts.count_proposal(store_path, proposal_id)
    texts = proposals.field_texts(body)
    field_defs = {str(f.get("id")): f for f in eff.get("fields", [])}
    fields = []
    for position, info in enumerate(counted["fields"], start=1):
        definition = field_defs.get(info["id"], {})
        fields.append(
            {
                "order": position,
                "id": info["id"],
                "label": info["label"],
                "kind": definition.get("kind", "text"),
                "audience": definition.get("audience", "public"),
                "required": info["required"],
                "text": texts.get(info["id"], ""),
                "chars": info["chars"],
                "limit": info["limit"],
                "limit_status": info["limit_status"],
                "status": info["status"],
                "flags": _flags(info),
            }
        )
    bio_info = dict(counted["bio"])
    bio_on_form = bio_info.get("on_form", True)
    # Nothing to paste when the form has no bio: no text and no flags.
    bio_info["text"] = proposals.bio_text(body) if bio_on_form else ""
    bio_info["variation"] = meta.get("bio_variation")
    bio_info["flags"] = _flags(counted["bio"]) if bio_on_form else []
    warnings = []
    unverified = [f["id"] for f in fields if f["limit"] is not None and f["limit_status"] == "unverified"]
    if unverified or (bio_info["limit"] is not None and bio_info["limit_status"] == "unverified"):
        warnings.append(
            "Some limits are approximate (unverified): the live form may differ. Confirm them with screenshots via /cfp:profile refresh."
        )
    if counted["over"]:
        warnings.append("Fields over their limit: " + ", ".join(counted["over"]))
    if counted["missing_required"]:
        warnings.append("Required fields not drafted: " + ", ".join(counted["missing_required"]))
    return {
        "proposal": proposal_id,
        "talk": meta.get("talk"),
        "profile": meta.get("profile"),
        "event": meta.get("event"),
        "event_name": (eff.get("event") or {}).get("name", ""),
        "session_type": meta.get("session_type"),
        "status": meta.get("status"),
        "fields": fields,
        "bio": bio_info,
        "over": counted["over"],
        "missing_required": counted["missing_required"],
        "warnings": warnings,
    }


def to_markdown(data):
    lines = [f"# Paste view: {data['proposal']}", ""]
    header = f"Event: {data['event_name'] or data['event']} ({data['event']}) | Session type: {data['session_type']} | Status: {data['status']}"
    lines.append(header)
    lines.append("")
    for warning in data["warnings"]:
        lines.append(f"Warning: {warning}")
    if data["warnings"]:
        lines.append("")
    for field in data["fields"]:
        audience = "reviewer-only" if field["audience"] == "reviewer" else "public"
        required = "required" if field["required"] else "optional"
        lines.append(f"## {field['order']}. {field['label']} ({field['id']}, {audience}, {required})")
        lines.append("")
        flag_text = f" [{', '.join(field['flags'])}]" if field["flags"] else ""
        lines.append(_count_label(field) + flag_text)
        lines.append("")
        lines.append(field["text"] if field["text"] else "(empty)")
        lines.append("")
    bio = data["bio"]
    if not bio.get("on_form", True):
        return "\n".join(lines)
    variation = f" (variation: {bio['variation']})" if bio.get("variation") else ""
    lines.append(f"## Speaker bio{variation}")
    lines.append("")
    flag_text = f" [{', '.join(bio['flags'])}]" if bio["flags"] else ""
    lines.append(_count_label(bio) + flag_text)
    lines.append("")
    lines.append(bio["text"] if bio["text"] else "(empty)")
    lines.append("")
    return "\n".join(lines)


def render(store_path, proposal_id, fmt="markdown"):
    if fmt not in FORMATS:
        raise CfpError(f"unknown format '{fmt}'; use markdown or json")
    data = build(store_path, proposal_id)
    if fmt == "json":
        return data
    return to_markdown(data)
