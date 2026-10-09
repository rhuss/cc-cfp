"""Character counts and limit evaluation for every field of a proposal."""

from cfplib import proposals


def count_proposal(store_path, proposal_id):
    _, meta, body = proposals.load_proposal(store_path, proposal_id)
    eff = proposals.effective_for(store_path, meta)
    texts = proposals.field_texts(body)
    fields = []
    over = []
    missing_required = []
    for field in eff.get("fields", []):
        field_id = str(field.get("id"))
        text = texts.get(field_id, "")
        result = proposals.field_result(field, text)
        drafted = result["chars"] > 0
        required = bool(field.get("required", False))
        if result["status"] == "over":
            over.append(field_id)
        if required and not drafted:
            missing_required.append(field_id)
        entry = {"id": field_id, "label": field.get("label", field_id), "required": required}
        entry.update({k: v for k, v in result.items() if k != "field"})
        entry["drafted"] = drafted
        fields.append(entry)
    bio_info = proposals.bio_result(eff, proposals.bio_text(body))
    bio_info["drafted"] = bio_info["chars"] > 0
    return {
        "proposal": proposal_id,
        "event": meta.get("event"),
        "fields": fields,
        "bio": bio_info,
        "over": over,
        "missing_required": missing_required,
    }
