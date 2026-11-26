"""Tests for proposal status transitions and side effects (cfplib.lifecycle)."""

import pytest

from cfplib import CfpError, frontmatter, lifecycle, profile, store
from conftest import TEMPLATES_DIR

TODAY = "2026-10-09"


def make_talk(store_path, talk_id="my-talk", **meta_overrides):
    meta, body = frontmatter.load(TEMPLATES_DIR / "talk.md")
    meta.update({"id": talk_id, "title": talk_id.replace("-", " ").title()})
    meta.update(meta_overrides)
    body = frontmatter.set_section(body, "Problem", "A problem.")
    store.save(store.talk_path(store_path, talk_id), meta, body)
    return talk_id


def make_proposal(store_path, talk_id="my-talk", event_id="kubecon-eu-2027", status="draft", fields=None, **meta_overrides):
    meta, body = frontmatter.load(TEMPLATES_DIR / "proposal.md")
    proposal_id = store.proposal_id(event_id, talk_id)
    meta.update({"id": proposal_id, "talk": talk_id, "profile": "kubecon", "event": event_id, "status": status})
    meta.update(meta_overrides)
    fields = fields or {"title": "A Title", "abstract": "An abstract.", "value_to_community": "Benefits text."}
    for field_id, text in fields.items():
        body = frontmatter.set_section(body, f"Field: {field_id}", text)
    store.save(store.proposal_path(store_path, proposal_id), meta, body)
    return proposal_id


@pytest.fixture
def prepared(seeded_store):
    make_talk(seeded_store)
    pid = make_proposal(seeded_store)
    return seeded_store, pid


def load_meta(store_path, proposal_id):
    return store.load(store.proposal_path(store_path, proposal_id))[0]


def test_transitions_table_matches_data_model():
    t = lifecycle.TRANSITIONS
    assert set(t["draft"]) == {"ready", "submitted", "withdrawn"}
    assert set(t["ready"]) == {"draft", "submitted", "withdrawn"}
    assert set(t["submitted"]) == {"accepted", "rejected", "withdrawn"}
    assert set(t["accepted"]) == {"presented", "withdrawn"}
    assert t["rejected"] == [] and t["withdrawn"] == [] and t["presented"] == []


def test_ready_back_to_draft_clears_ready_on_and_accepted_can_withdraw(seeded_store):
    make_talk(seeded_store)
    pid = make_proposal(seeded_store, status="ready", ready_on="2026-10-01")
    result = lifecycle.set_status(seeded_store, pid, "draft", today=TODAY)
    meta = load_meta(seeded_store, pid)
    assert result["to"] == "draft" and meta["status"] == "draft" and meta["ready_on"] is None
    assert meta["preflight"] == {}
    assert any("ready_on cleared" in effect for effect in result["side_effects"])
    pid2 = make_proposal(seeded_store, event_id="kubecon-na-2026", status="accepted")
    lifecycle.set_status(seeded_store, pid2, "withdrawn", date="2026-11-01", today=TODAY)
    meta = load_meta(seeded_store, pid2)
    assert meta["status"] == "withdrawn" and meta["decided_on"] == "2026-11-01"


def test_content_edit_demotes_ready_to_draft(seeded_store):
    from cfplib import proposals

    make_talk(seeded_store)
    passing = [{"round": 1, "date": TODAY, "scores": {}, "comments": {}, "verdict": "pass", "suggestions": []}]
    clean = {"date": TODAY, "ok": True, "findings": []}
    pid = make_proposal(seeded_store, status="ready", ready_on="2026-10-01", review_rounds=passing, preflight=clean)
    assert lifecycle.ready_check(seeded_store, pid)["can_ready"] is True
    result = proposals.set_field(seeded_store, pid, "abstract", "Edited after ready.", today=TODAY)
    assert result["reset_to_draft"] is True
    meta = load_meta(seeded_store, pid)
    assert meta["status"] == "draft" and meta["ready_on"] is None
    # the stale review and pre-flight cannot carry the proposal back to ready
    assert meta["preflight"] == {} and meta["review_stale"] is True and len(meta["review_rounds"]) == 1
    check = lifecycle.ready_check(seeded_store, pid)
    assert check["can_ready"] is False and any("edited after" in r for r in check["reasons"])
    with pytest.raises(CfpError):
        lifecycle.set_status(seeded_store, pid, "ready", today=TODAY)
    # a draft stays a draft, and the key is absent when nothing changed
    assert "reset_to_draft" not in proposals.set_field(seeded_store, pid, "abstract", "Again.", today=TODAY)
    pid2 = make_proposal(seeded_store, event_id="kubecon-na-2026", status="ready", ready_on="2026-10-01")
    assert proposals.set_bio_text(seeded_store, pid2, "Bio.", today=TODAY)["reset_to_draft"] is True
    pid3 = make_proposal(seeded_store, "other-talk", status="ready", ready_on="2026-10-01")
    make_talk(seeded_store, "other-talk")
    assert proposals.set_meta(seeded_store, pid3, track="Security", today=TODAY)["reset_to_draft"] is True
    assert load_meta(seeded_store, pid3)["status"] == "draft"


def test_set_status_tolerates_missing_id_key(seeded_store):
    make_talk(seeded_store)
    pid = make_proposal(seeded_store, status="submitted")
    path = store.proposal_path(seeded_store, pid)
    meta, body = store.load(path)
    del meta["id"]
    store.save(path, meta, body)
    result = lifecycle.set_status(seeded_store, pid, "accepted", date="2026-12-07", today=TODAY)
    assert result["to"] == "accepted"
    examples, _ = profile.list_examples(seeded_store, "kubecon")
    assert any(e["proposal"] == pid for e in examples)


def test_submitted_sets_date(prepared):
    s, pid = prepared
    result = lifecycle.set_status(s, pid, "submitted", date="2026-10-10", today=TODAY)
    assert result["from"] == "draft" and result["to"] == "submitted" and result["date"] == "2026-10-10"
    meta = load_meta(s, pid)
    assert meta["status"] == "submitted" and meta["submitted_on"] == "2026-10-10"
    assert meta["updated"] == TODAY


def test_default_date_is_today(prepared):
    s, pid = prepared
    result = lifecycle.set_status(s, pid, "submitted", today=TODAY)
    assert result["date"] == TODAY
    assert load_meta(s, pid)["submitted_on"] == TODAY


def test_disallowed_transition_lists_allowed_targets(prepared):
    s, pid = prepared
    with pytest.raises(CfpError) as info:
        lifecycle.set_status(s, pid, "accepted", today=TODAY)
    message = str(info.value)
    assert "draft" in message and "accepted" in message
    assert "ready" in message and "submitted" in message and "withdrawn" in message
    with pytest.raises(CfpError):
        lifecycle.set_status(s, pid, "bogus", today=TODAY)
    assert load_meta(s, pid)["status"] == "draft"


def test_rejected_and_withdrawn_set_decided_on(seeded_store):
    make_talk(seeded_store)
    pid = make_proposal(seeded_store, status="submitted", submitted_on="2026-10-01")
    result = lifecycle.set_status(seeded_store, pid, "rejected", date="2026-12-07", today=TODAY)
    assert load_meta(seeded_store, pid)["decided_on"] == "2026-12-07"
    pid2 = make_proposal(seeded_store, event_id="kubecon-na-2026", status="draft")
    result2 = lifecycle.set_status(seeded_store, pid2, "withdrawn", today=TODAY)
    meta = load_meta(seeded_store, pid2)
    assert meta["status"] == "withdrawn" and meta["decided_on"] == TODAY
    # US4 scenario 3, negative half: neither transition touches the talk's history
    talk_meta, _ = store.load(store.talk_path(seeded_store, "my-talk"))
    assert talk_meta["outings"] == []
    assert result["side_effects"] == [] and result2["side_effects"] == []
    examples, _ = profile.list_examples(seeded_store, "kubecon")
    assert not any(e["origin"] == "own-accepted" for e in examples)


def test_status_set_rejects_invalid_date(prepared):
    s, pid = prepared
    with pytest.raises(CfpError, match="ISO"):
        lifecycle.set_status(s, pid, "submitted", date="next week", today=TODAY)
    assert load_meta(s, pid)["status"] == "draft"


def test_accepted_creates_calibration_example(seeded_store):
    make_talk(seeded_store)
    pid = make_proposal(seeded_store, status="submitted")
    result = lifecycle.set_status(seeded_store, pid, "accepted", date="2026-12-07", today=TODAY)
    assert any("calibration example" in effect for effect in result["side_effects"])
    meta = load_meta(seeded_store, pid)
    assert meta["status"] == "accepted" and meta["decided_on"] == "2026-12-07"
    examples, _ = profile.list_examples(seeded_store, "kubecon")
    own = [e for e in examples if e["origin"] == "own-accepted"]
    assert len(own) == 1
    assert own[0]["id"] == pid and own[0]["proposal"] == pid
    assert own[0]["title"] == "A Title" and own[0]["abstract"] == "An abstract." and own[0]["benefits"] == "Benefits text."
    assert own[0]["event"] == "kubecon-eu-2027" and own[0]["year"] == 2027


def test_presented_records_outing_on_talk(seeded_store):
    make_talk(seeded_store)
    pid = make_proposal(seeded_store, status="accepted")
    result = lifecycle.set_status(seeded_store, pid, "presented", date="2027-03-16", today=TODAY)
    assert any("outing" in effect for effect in result["side_effects"])
    assert load_meta(seeded_store, pid)["presented_on"] == "2027-03-16"
    talk_meta, _ = store.load(store.talk_path(seeded_store, "my-talk"))
    assert talk_meta["outings"] == [
        {"event": "kubecon-eu-2027", "family": "kubecon", "date": "2027-03-16", "link": "", "kind": "presented"}
    ]


def test_ready_requires_pass_and_preflight_unless_forced(prepared):
    s, pid = prepared
    check = lifecycle.ready_check(s, pid)
    assert check["can_ready"] is False and len(check["reasons"]) == 2
    with pytest.raises(CfpError):
        lifecycle.set_status(s, pid, "ready", today=TODAY)

    path = store.proposal_path(s, pid)
    meta, body = store.load(path)
    meta["review_rounds"] = [{"round": 1, "date": TODAY, "scores": {}, "comments": {}, "verdict": "revise", "suggestions": []}]
    meta["preflight"] = {"date": TODAY, "ok": True, "findings": []}
    store.save(path, meta, body)
    check = lifecycle.ready_check(s, pid)
    assert check["can_ready"] is False and "pass" in check["reasons"][0]

    meta["review_rounds"].append({"round": 2, "date": TODAY, "scores": {}, "comments": {}, "verdict": "pass", "suggestions": []})
    meta["preflight"] = {"date": TODAY, "ok": False, "findings": [{"rule": "x", "severity": "disqualify", "text": "t"}]}
    store.save(path, meta, body)
    check = lifecycle.ready_check(s, pid)
    assert check["can_ready"] is False and "pre-flight" in check["reasons"][0]

    meta["preflight"]["ok"] = True
    store.save(path, meta, body)
    assert lifecycle.ready_check(s, pid) == {"can_ready": True, "reasons": []}
    result = lifecycle.set_status(s, pid, "ready", today=TODAY)
    assert result["to"] == "ready" and load_meta(s, pid)["ready_on"] == TODAY


def test_ready_forced(prepared):
    s, pid = prepared
    result = lifecycle.set_status(s, pid, "ready", force=True, today=TODAY)
    assert result["to"] == "ready"
    assert any("forced" in effect for effect in result["side_effects"])


def test_count_submissions_by_status(seeded_store):
    for n, status in enumerate(["submitted", "accepted", "rejected", "presented", "draft", "ready", "withdrawn"]):
        make_talk(seeded_store, f"talk-{n}")
        make_proposal(seeded_store, f"talk-{n}", status=status)
    make_talk(seeded_store, "other")
    make_proposal(seeded_store, "other", event_id="kubecon-na-2026", status="submitted")
    assert lifecycle.count_submissions(seeded_store, "kubecon-eu-2027") == (4, [])
    assert lifecycle.count_submissions(seeded_store, "kubecon-eu-2027", exclude_proposal="kubecon-eu-2027--talk-0") == (3, [])
    assert lifecycle.count_submissions(seeded_store, "kubecon-na-2026") == (1, [])
    assert lifecycle.count_submissions(seeded_store, "kubecon-india-2026") == (0, [])

    # a sync "conflicted copy" of a counted proposal shares its id and counts once
    original = store.proposal_path(seeded_store, "kubecon-eu-2027--talk-0")
    (original.parent / "kubecon-eu-2027--talk-0 (conflicted copy).md").write_text(original.read_text())
    assert lifecycle.count_submissions(seeded_store, "kubecon-eu-2027")[0] == 4
    # an unparseable proposal file is reported, not silently dropped
    (original.parent / "broken.md").write_text("---\nstatus: submitted\nevent: kubecon-eu-2027\n  bad: indent\n---\n")
    count, problems = lifecycle.count_submissions(seeded_store, "kubecon-eu-2027")
    assert count == 4 and len(problems) == 1 and problems[0]["path"].endswith("broken.md")


def test_unknown_proposal(seeded_store):
    with pytest.raises(CfpError):
        lifecycle.set_status(seeded_store, "nope--nope", "submitted", today=TODAY)
