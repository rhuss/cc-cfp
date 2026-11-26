"""Tests for proposal operations (cfplib.proposals) and the proposal CLI group."""

import pytest

from cfplib import CfpError, bios, frontmatter, profile, proposals, store, talks

TODAY = "2026-10-09"
EVENT = "kubecon-eu-2027"


@pytest.fixture
def with_talk(seeded_store):
    talks.write_talk(seeded_store, "my-talk", {"title": "My Talk", "personas": ["SREs"], "sections": {"Problem": "P"}}, today=TODAY)
    return seeded_store


def test_create_proposal(with_talk):
    s = with_talk
    result = proposals.create(s, "my-talk", "kubecon", EVENT, "session", angle="problem-first", today=TODAY)
    assert result["id"] == f"{EVENT}--my-talk"
    assert result["path"].endswith(f"proposals/{EVENT}--my-talk.md")
    shown = proposals.show(s, result["id"])
    assert shown["talk"] == "my-talk" and shown["profile"] == "kubecon" and shown["event"] == EVENT
    assert shown["session_type"] == "session" and shown["angle"] == "problem-first"
    assert shown["status"] == "draft" and shown["created"] == TODAY
    assert shown["fields"] == {} and shown["bio"] == ""
    assert shown["review_rounds"] == [] and shown["preflight"] == {} and shown["voice_pass"] is False
    assert shown["co_speakers"] == [] and shown["resources"] == []


def test_create_refusals(with_talk):
    s = with_talk
    with pytest.raises(CfpError, match="unknown talk"):
        proposals.create(s, "nope", "kubecon", EVENT, "session", today=TODAY)
    with pytest.raises(CfpError, match="session type"):
        proposals.create(s, "my-talk", "kubecon", EVENT, "keynote", today=TODAY)
    with pytest.raises(CfpError, match="unknown event"):
        proposals.create(s, "my-talk", "kubecon", "kubecon-india-2026", "session", today=TODAY)
    proposals.create(s, "my-talk", "kubecon", EVENT, "session", today=TODAY)
    with pytest.raises(CfpError, match="already exists"):
        proposals.create(s, "my-talk", "kubecon", EVENT, "session", today=TODAY)
    profile.approve(s, "kubecon", event_id="kubecon-na-2026", approved=False)
    with pytest.raises(CfpError, match="not approved"):
        proposals.create(s, "my-talk", "kubecon", "kubecon-na-2026", "session", today=TODAY)
    profile.approve(s, "kubecon", approved=False)
    with pytest.raises(CfpError, match="not approved"):
        proposals.create(s, "my-talk", "kubecon", EVENT, "session", today=TODAY)


@pytest.fixture
def with_proposal(with_talk):
    result = proposals.create(with_talk, "my-talk", "kubecon", EVENT, "session", today=TODAY)
    return with_talk, result["id"]


def test_set_field_writes_section_and_reports_status(with_proposal):
    s, pid = with_proposal
    result = proposals.set_field(s, pid, "title", "A Specific Title\r\n", today=TODAY)
    assert result == {"field": "title", "chars": 16, "limit": 75, "limit_status": "unverified", "status": "unverified"}
    over = proposals.set_field(s, pid, "title", "x" * 80, today=TODAY)
    assert over["status"] == "over" and over["chars"] == 80
    nolimit = proposals.set_field(s, pid, "cncf_oss_projects", "Kubernetes, Argo", today=TODAY)
    assert nolimit["status"] == "no-limit" and nolimit["limit"] is None
    shown = proposals.show(s, pid)
    assert shown["fields"]["title"] == "x" * 80
    assert shown["fields"]["cncf_oss_projects"] == "Kubernetes, Argo"
    assert shown["updated"] == TODAY


def test_set_field_ok_status_for_verified_limit(with_proposal):
    s, pid = with_proposal
    path = store.profile_path(s, "kubecon")
    meta, body = frontmatter.load(path)
    for field in meta["fields"]:
        if field["id"] == "title":
            field["limit_status"] = "screenshot"
    frontmatter.save(path, meta, body)
    assert proposals.set_field(s, pid, "title", "Short", today=TODAY)["status"] == "ok"


def test_set_field_unknown_field(with_proposal):
    s, pid = with_proposal
    with pytest.raises(CfpError) as info:
        proposals.set_field(s, pid, "bogus", "x", today=TODAY)
    assert "bogus" in str(info.value) and "title" in str(info.value)


def test_set_field_choice_validation_and_meta_sync(with_proposal):
    s, pid = with_proposal
    result = proposals.set_field(s, pid, "audience_level", "intermediate", today=TODAY)
    assert result["status"] == "no-limit"
    shown = proposals.show(s, pid)
    assert shown["fields"]["audience_level"] == "Intermediate"
    assert shown["audience_level"] == "Intermediate"
    with pytest.raises(CfpError, match="Any, Beginner"):
        proposals.set_field(s, pid, "audience_level", "Expert", today=TODAY)
    proposals.set_field(s, pid, "track", "security", today=TODAY)
    assert proposals.show(s, pid)["track"] == "Security"
    # track membership is a pre-flight rule, so unknown tracks are stored as typed
    proposals.set_field(s, pid, "track", "Not A Track", today=TODAY)
    assert proposals.show(s, pid)["track"] == "Not A Track"
    proposals.set_field(s, pid, "case_study", "yes", today=TODAY)
    assert proposals.show(s, pid)["fields"]["case_study"] == "Yes"
    with pytest.raises(CfpError):
        proposals.set_field(s, pid, "case_study", "maybe", today=TODAY)


def test_fields_are_kept_in_form_order(with_proposal):
    s, pid = with_proposal
    proposals.set_field(s, pid, "value_to_community", "B", today=TODAY)
    proposals.set_field(s, pid, "title", "T", today=TODAY)
    proposals.set_bio_text(s, pid, "Bio", today=TODAY)
    proposals.set_field(s, pid, "abstract", "A", today=TODAY)
    _, body = store.load(store.proposal_path(s, pid))
    assert list(frontmatter.sections(body).keys()) == ["Field: title", "Field: abstract", "Field: value_to_community", "Bio"]


def test_set_meta_updates_keys_and_bio_snapshot(with_proposal):
    s, pid = with_proposal
    bios.write_bio(s, "short", "cloud-native", 450, "Test Speaker builds things.", today=TODAY)
    bios.write_resource(s, {"id": "rec", "type": "recording", "title": "Rec", "link": "https://r"})
    result = proposals.set_meta(
        s,
        pid,
        track="Security",
        audience_level="Advanced",
        bio="short",
        resources=["rec"],
        co_speakers=["Ada Lovelace, Example Corp"],
        co_speaker_genders=["woman"],
        angle="story",
        today=TODAY,
    )
    assert set(result["updated"]) == {"track", "audience_level", "bio_variation", "resources", "co_speakers", "co_speaker_genders", "angle", "bio"}
    shown = proposals.show(s, pid)
    assert shown["track"] == "Security" and shown["fields"]["track"] == "Security"
    assert shown["audience_level"] == "Advanced" and shown["fields"]["audience_level"] == "Advanced"
    assert shown["bio_variation"] == "short" and shown["bio"] == "Test Speaker builds things."
    assert shown["resources"] == ["rec"] and shown["fields"]["resources"] == "Rec: https://r"
    assert shown["co_speakers"] == ["Ada Lovelace, Example Corp"] and shown["co_speaker_genders"] == ["woman"]
    assert shown["angle"] == "story"


def test_set_meta_validations(with_proposal):
    s, pid = with_proposal
    with pytest.raises(CfpError, match="unknown bio"):
        proposals.set_meta(s, pid, bio="nope", today=TODAY)
    with pytest.raises(CfpError, match="unknown resource"):
        proposals.set_meta(s, pid, resources=["nope"], today=TODAY)
    assert proposals.set_meta(s, pid, track="Nope", today=TODAY)["updated"] == ["track"]
    assert proposals.show(s, pid)["fields"]["track"] == "Nope"
    with pytest.raises(CfpError, match="session type"):
        proposals.set_meta(s, pid, session_type="keynote", today=TODAY)
    assert proposals.set_meta(s, pid, session_type="panel", today=TODAY)["updated"] == ["session_type"]


def test_set_bio_text_replaces_only_snapshot(with_proposal):
    s, pid = with_proposal
    bios.write_bio(s, "short", "cloud-native", 450, "Original stored bio.", today=TODAY)
    proposals.set_meta(s, pid, bio="short", today=TODAY)
    result = proposals.set_bio_text(s, pid, "Shortened snapshot.", today=TODAY)
    assert result == {"chars": 19, "limit": 500, "limit_status": "screenshot", "status": "ok"}
    assert proposals.show(s, pid)["bio"] == "Shortened snapshot."
    assert proposals.show(s, pid)["bio_variation"] == "short"
    assert bios.show_bio(s, "short")["text"] == "Original stored bio."
    assert proposals.set_bio_text(s, pid, "x" * 501, today=TODAY)["status"] == "over"


def test_mark_voice_pass(with_proposal):
    s, pid = with_proposal
    assert proposals.mark_voice_pass(s, pid, today=TODAY) == {"voice_pass": True}
    assert proposals.show(s, pid)["voice_pass"] is True


def test_list_proposals_filters_and_groups(seeded_store):
    for n, (event, status) in enumerate([(EVENT, "draft"), (EVENT, "submitted"), ("kubecon-na-2026", "draft"), (EVENT, "rejected")]):
        talks.write_talk(seeded_store, f"t{n}", {"title": f"T{n}"}, today=TODAY)
        pid = proposals.create(seeded_store, f"t{n}", "kubecon", event, "session", today=TODAY)["id"]
        proposals.set_field(seeded_store, pid, "title", f"Title {n}", today=TODAY)
        if status != "draft":
            path = store.proposal_path(seeded_store, pid)
            meta, body = store.load(path)
            meta["status"] = status
            meta["submitted_on"] = "2026-10-01"
            store.save(path, meta, body)
    (seeded_store / "proposals" / "broken.md").write_text("---\nid: broken\n", encoding="utf-8")

    listing, problems = proposals.list_proposals(seeded_store)
    assert len(problems) == 1
    assert [p["status"] for p in listing] == ["draft", "draft", "submitted", "rejected"]
    assert listing[0]["title"] == "Title 0" and listing[0]["talk"] == "t0" and listing[0]["submitted_on"] is None
    assert listing[0]["profile"] == "kubecon" and listing[0]["event"] == EVENT
    assert listing[1]["event"] == "kubecon-na-2026"
    assert listing[2]["submitted_on"] == "2026-10-01"
    drafts, _ = proposals.list_proposals(seeded_store, status="draft")
    assert len(drafts) == 2
    eu, _ = proposals.list_proposals(seeded_store, event=EVENT)
    assert len(eu) == 3
    by_talk, _ = proposals.list_proposals(seeded_store, talk="t3")
    assert [p["id"] for p in by_talk] == [f"{EVENT}--t3"]


def test_proposal_cli(with_talk, run_cli, write_text):
    s = with_talk
    bios.write_bio(s, "short", "cloud-native", 450, "Bio text.", today=TODAY)
    created = run_cli("proposal", "create", "--talk", "my-talk", "--profile", "kubecon", "--event", EVENT, "--session-type", "session", "--angle", "problem-first")
    pid = created["id"]
    assert pid == f"{EVENT}--my-talk"
    dup = run_cli("proposal", "create", "--talk", "my-talk", "--profile", "kubecon", "--event", EVENT, "--session-type", "session", expect_ok=False)
    assert dup.code == 1 and "already exists" in dup.data["error"]
    field = run_cli("proposal", "set-field", "--proposal", pid, "--field", "title", "--text-file", write_text("A Title"))
    assert field["chars"] == 7 and field["status"] == "unverified"
    bad = run_cli("proposal", "set-field", "--proposal", pid, "--field", "bogus", "--text-file", write_text("x"), expect_ok=False)
    assert bad.code == 1
    meta = run_cli("proposal", "set-meta", "--proposal", pid, "--track", "Security", "--audience-level", "Intermediate", "--bio", "short", "--co-speakers", '["Ada, Corp"]')
    assert "bio" in meta["updated"] and "track" in meta["updated"]
    shown = run_cli("proposal", "show", "--proposal", pid)
    assert shown["bio"] == "Bio text." and shown["fields"]["track"] == "Security" and shown["co_speakers"] == ["Ada, Corp"]
    snap = run_cli("proposal", "set-bio-text", "--proposal", pid, "--text-file", write_text("Shorter bio."))
    assert snap["chars"] == 12
    assert run_cli("proposal", "mark-voice-pass", "--proposal", pid)["voice_pass"] is True
    listing = run_cli("proposal", "list", "--status", "draft")
    assert listing["proposals"][0]["id"] == pid and listing["proposals"][0]["title"] == "A Title"
    assert listing["proposals"][0]["profile"] == "kubecon" and listing["proposals"][0]["event"] == EVENT
    assert listing["problems"] == []


def test_set_meta_from_json_file_keeps_free_text_off_the_command_line(with_talk, run_cli, write_json):
    s = with_talk
    pid = run_cli("proposal", "create", "--talk", "my-talk", "--profile", "kubecon", "--event", EVENT, "--session-type", "session")["id"]
    values = {"track": "Security", "angle": "story with `backticks` and $(subshell)", "co_speakers": ["Ada, Corp"], "resources": ""}
    meta = run_cli("proposal", "set-meta", "--proposal", pid, "--from-json", write_json(values))
    assert set(meta["updated"]) == {"track", "angle", "co_speakers", "resources"}
    shown = run_cli("proposal", "show", "--proposal", pid)
    assert shown["angle"] == "story with `backticks` and $(subshell)" and shown["track"] == "Security"
    # flags win over the file
    meta = run_cli("proposal", "set-meta", "--proposal", pid, "--from-json", write_json({"track": "Observability"}), "--track", "Connectivity")
    assert run_cli("proposal", "show", "--proposal", pid)["track"] == "Connectivity"
    bad = run_cli("proposal", "set-meta", "--proposal", pid, "--from-json", write_json({"nope": 1}), expect_ok=False)
    assert bad.code == 1 and "nope" in bad["error"]
    bad = run_cli("proposal", "set-meta", "--proposal", pid, "--from-json", write_json(["list"]), expect_ok=False)
    assert bad.code == 1 and "JSON object" in bad["error"]
    bad = run_cli("proposal", "set-meta", "--proposal", pid, "--from-json", write_json({"co_speakers": "Ada, Corp"}), expect_ok=False)
    assert bad.code == 1 and "co_speakers" in bad["error"] and "list" in bad["error"]
    assert run_cli("proposal", "show", "--proposal", pid)["co_speakers"] == ["Ada, Corp"]


def test_list_reports_non_utf8_file_as_problem_not_traceback(seeded_store, run_cli):
    (seeded_store / "proposals" / "latin.md").write_bytes(b"---\nid: caf\xe9\n---\n")
    result = run_cli("proposal", "list")
    assert result["proposals"] == [] and len(result["problems"]) == 1
    assert "UTF-8" in result["problems"][0]["error"]


def test_unexpected_exception_still_yields_json(seeded_store, run_cli, monkeypatch):
    # a directory with an .md name is an OSError at read time, which must not escape as a traceback
    (seeded_store / "talks" / "dir.md").mkdir()
    result = run_cli("talk", "show", "--talk", "dir", expect_ok=False)
    assert result.code == 1 and result["ok"] is False and "error" in result.data
