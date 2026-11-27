"""Tests for the committee review packet and round recording (cfplib.review)."""

import pytest

from cfplib import CfpError, bios, profile, proposals, review, talks

TODAY = "2026-10-09"
EVENT = "kubecon-eu-2027"
CRITERIA = ["content", "originality", "relevance", "speaker", "not_product_pitch"]


@pytest.fixture
def pid(seeded_store):
    s = seeded_store
    talks.write_talk(
        s,
        "t",
        {"title": "T", "personas": ["SREs"], "projects": ["Kubernetes"], "sections": {"Problem": "P", "Takeaways": "- a\n- b"}},
        today=TODAY,
    )
    pid = proposals.create(s, "t", "kubecon", EVENT, "session", angle="problem-first", today=TODAY)["id"]
    proposals.set_field(s, pid, "title", "A Title", today=TODAY)
    proposals.set_field(s, pid, "abstract", "An abstract.", today=TODAY)
    proposals.set_field(s, pid, "value_to_community", "Benefits.", today=TODAY)
    proposals.set_field(s, pid, "audience_level", "Intermediate", today=TODAY)
    proposals.set_field(s, pid, "track", "Security", today=TODAY)
    bios.write_bio(s, "b", "ai", 500, "Bio.", today=TODAY)
    bios.write_resource(s, {"id": "rec", "type": "recording", "title": "Rec", "link": "https://r"})
    proposals.set_meta(s, pid, bio="b", resources=["rec"], today=TODAY)
    return pid


def reviewer_json(scores=None, verdict="revise", suggestions=None, comments=None):
    scores = scores or {c: 4.0 for c in CRITERIA}
    comments = comments if comments is not None else {c: f"Comment on {c}." for c in scores}
    return {
        "scores": scores,
        "comments": comments,
        "verdict": verdict,
        "suggestions": suggestions if suggestions is not None else [{"field": "abstract", "text": "State the takeaways."}],
    }


def test_packet_contents(seeded_store, pid):
    for n in range(4):
        profile.add_example(seeded_store, "kubecon", {"title": f"Ex {n}", "abstract": "A", "benefits": "B", "event": "e", "year": 2020 + n, "origin": "manual"}, today=f"2026-11-0{n + 1}")
    packet = review.packet(seeded_store, pid)["packet"]
    assert packet["proposal"] == pid and packet["profile"] == "kubecon" and packet["event"] == EVENT
    assert [c["id"] for c in packet["rubric"]["criteria"]] == CRITERIA
    assert packet["rubric"]["scale_max"] == 5
    assert packet["thresholds"] == {"pass_average": 4.0, "pass_min_criterion": 3.0}
    assert len(packet["rejection_reasons"]) >= 5
    assert len(packet["examples"]) == 3
    assert packet["examples"][0]["title"] == "Ex 3"
    assert all(set(e) >= {"title", "abstract", "benefits", "event", "year", "origin"} for e in packet["examples"])
    assert packet["fields"][0] == {"id": "title", "label": "Session Title", "kind": "text", "audience": "public", "required": True, "text": "A Title"}
    value = next(f for f in packet["fields"] if f["id"] == "value_to_community")
    assert value["audience"] == "reviewer" and value["kind"] == "longtext"
    assert packet["relevance_field"] == "value_to_community"
    assert packet["audience_level"] == "Intermediate" and packet["track"] == "Security"
    assert packet["session_type"]["id"] == "session" and packet["session_type"]["duration_min"] == 30
    assert packet["bio"] == "Bio."
    assert packet["resources"] == [{"id": "rec", "type": "recording", "title": "Rec", "link": "https://r"}]
    assert packet["talk"]["title"] == "T" and packet["talk"]["personas"] == ["SREs"]
    assert "drafting_guidance" in packet and packet["round"] == 1
    fewer = review.packet(seeded_store, pid, examples=1)["packet"]
    assert len(fewer["examples"]) == 1


def test_record_rejects_missing_criterion_and_bad_values(seeded_store, pid):
    data = reviewer_json()
    del data["scores"]["speaker"]
    with pytest.raises(CfpError, match="speaker"):
        review.record(seeded_store, pid, data, today=TODAY)
    data = reviewer_json()
    data["scores"]["content"] = 6
    with pytest.raises(CfpError, match="content"):
        review.record(seeded_store, pid, data, today=TODAY)
    data = reviewer_json()
    del data["comments"]["relevance"]
    with pytest.raises(CfpError, match="relevance"):
        review.record(seeded_store, pid, data, today=TODAY)
    data = reviewer_json(suggestions=[{"text": "no field"}])
    with pytest.raises(CfpError, match="field"):
        review.record(seeded_store, pid, data, today=TODAY)
    with pytest.raises(CfpError):
        review.record(seeded_store, pid, {"scores": "bad"}, today=TODAY)
    data = reviewer_json()
    data["scores"]["content"] = True  # JSON true is not a score, even though bool is an int in Python
    with pytest.raises(CfpError, match="number"):
        review.record(seeded_store, pid, data, today=TODAY)
    assert review.history(seeded_store, pid)["rounds"] == []


def test_record_score_exactly_at_pass_min_criterion_passes(seeded_store, pid):
    scores = {c: 5.0 for c in CRITERIA}
    scores["content"] = 3.0  # equal to pass_min_criterion, so not below it
    result = review.record(seeded_store, pid, reviewer_json(scores=scores, verdict="pass"), today=TODAY)
    assert result["below_min"] == [] and result["verdict"] == "pass" and result["average"] == 4.6
    scores["content"] = 2.9
    result = review.record(seeded_store, pid, reviewer_json(scores=scores, verdict="pass"), today=TODAY)
    assert result["below_min"] == ["content"] and result["verdict"] == "revise"


def test_record_computes_verdict_from_thresholds(seeded_store, pid):
    first = review.record(seeded_store, pid, reviewer_json(scores={"content": 3.5, "originality": 4.0, "relevance": 4.5, "speaker": 4.0, "not_product_pitch": 5.0}, verdict="pass"), today=TODAY)
    assert first["round"] == 1 and first["verdict"] == "pass" and first["average"] == 4.2
    assert first["below_min"] == [] and first["reviewer_verdict"] == "pass"
    assert first["suggestions"] == [{"field": "abstract", "text": "State the takeaways."}]

    second = review.record(seeded_store, pid, reviewer_json(scores={"content": 2.5, "originality": 5.0, "relevance": 5.0, "speaker": 5.0, "not_product_pitch": 5.0}, verdict="pass"), today=TODAY)
    assert second["round"] == 2 and second["verdict"] == "revise" and second["below_min"] == ["content"]
    assert second["average"] == 4.5

    third = review.record(seeded_store, pid, reviewer_json(scores={c: 3.5 for c in CRITERIA}, verdict="pass"), today=TODAY)
    assert third["verdict"] == "revise" and third["below_min"] == [] and third["average"] == 3.5

    rounds = review.history(seeded_store, pid)["rounds"]
    assert [r["round"] for r in rounds] == [1, 2, 3]
    assert rounds[1]["verdict"] == "revise" and rounds[1]["reviewer_verdict"] == "pass"
    assert rounds[0]["date"] == TODAY and rounds[0]["scores"]["content"] == 3.5
    assert rounds[0]["comments"]["content"] == "Comment on content."
    assert proposals.show(seeded_store, pid)["review_rounds"][2]["round"] == 3
    assert review.packet(seeded_store, pid)["packet"]["round"] == 4


def test_record_limits_suggestions_and_tolerates_extra_keys(seeded_store, pid):
    suggestions = [{"field": "abstract", "text": f"s{n}"} for n in range(8)]
    data = reviewer_json(suggestions=suggestions)
    data["extra"] = "ignored"
    result = review.record(seeded_store, pid, data, today=TODAY)
    assert len(result["suggestions"]) == 5


def test_review_cli(seeded_store, pid, run_cli, write_json):
    packet = run_cli("review", "packet", "--proposal", pid, "--examples", "1")
    assert len(packet["packet"]["examples"]) == 1
    recorded = run_cli("review", "record", "--proposal", pid, "--from-json", write_json(reviewer_json()))
    assert recorded["round"] == 1 and recorded["verdict"] == "pass"
    bad = run_cli("review", "record", "--proposal", pid, "--from-json", write_json({"scores": {}}), expect_ok=False)
    assert bad.code == 1
    assert len(run_cli("review", "history", "--proposal", pid)["rounds"]) == 1
