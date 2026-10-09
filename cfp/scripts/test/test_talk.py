"""Tests for talk operations (cfplib.talks) and the talk CLI group."""

import pytest

from cfplib import CfpError, frontmatter, store, talks

TODAY = "2026-10-09"


def test_write_talk_creates_with_slug_from_title(seeded_store):
    result = talks.write_talk(
        seeded_store,
        None,
        {
            "title": "What Broke When We Put Agents on the Platform",
            "personas": ["Platform engineers"],
            "projects": ["Kubernetes"],
            "sections": {"Problem": "Agents misbehave.", "Takeaways": "- one\n- two"},
        },
        today=TODAY,
    )
    assert result["id"] == "what-broke-when-we-put-agents-on-the-platform"
    assert result["created"] is True
    assert result["path"].endswith("talks/what-broke-when-we-put-agents-on-the-platform.md")
    meta, body = store.load(store.talk_path(seeded_store, result["id"]))
    assert meta["id"] == result["id"]
    assert meta["status"] == "active"
    assert meta["created"] == TODAY and meta["updated"] == TODAY
    assert meta["personas"] == ["Platform engineers"]
    assert meta["outings"] == [] and meta["resources"] == [] and meta["source_material"] == []
    sections = frontmatter.sections(body)
    assert list(sections.keys()) == ["Problem", "Contribution", "Takeaways", "What is new", "Story notes"]
    assert sections["Problem"] == "Agents misbehave."
    assert sections["Takeaways"] == "- one\n- two"
    assert sections["Contribution"] == ""


def test_write_talk_updates_and_keeps_other_sections(seeded_store):
    talks.write_talk(seeded_store, "t1", {"title": "T1", "sections": {"Problem": "P"}}, today="2026-01-01")
    result = talks.write_talk(seeded_store, "t1", {"sections": {"Contribution": "C"}, "projects": ["Argo CD"]}, today=TODAY)
    assert result["created"] is False and result["id"] == "t1"
    shown = talks.show_talk(seeded_store, "t1")
    assert shown["sections"]["Problem"] == "P" and shown["sections"]["Contribution"] == "C"
    assert shown["title"] == "T1" and shown["projects"] == ["Argo CD"]
    assert shown["created"] == "2026-01-01" and shown["updated"] == TODAY


def test_write_talk_requires_title_for_new(seeded_store):
    with pytest.raises(CfpError):
        talks.write_talk(seeded_store, None, {"sections": {}}, today=TODAY)
    with pytest.raises(CfpError):
        talks.write_talk(seeded_store, "new-id", {}, today=TODAY)


def test_write_talk_rejects_invalid_outing_date(seeded_store):
    with pytest.raises(CfpError, match="invalid date 'April 2025'"):
        talks.write_talk(
            seeded_store,
            None,
            {
                "title": "Dated Talk",
                "outings": [{"event": "KubeCon EU 2025", "family": "kubecon", "date": "April 2025", "kind": "presented"}],
            },
            today=TODAY,
        )
    assert not store.talk_path(seeded_store, "dated-talk").exists()


def test_write_talk_accepts_iso_and_empty_outing_dates(seeded_store):
    result = talks.write_talk(
        seeded_store,
        None,
        {
            "title": "Dated Talk",
            "outings": [
                {"event": "KubeCon EU 2025", "family": "kubecon", "date": "2025-04-02", "kind": "presented"},
                {"event": "Meetup", "date": "", "kind": "presented"},
            ],
        },
        today=TODAY,
    )
    meta, _ = store.load(store.talk_path(seeded_store, result["id"]))
    assert [o["date"] for o in meta["outings"]] == ["2025-04-02", ""]


def test_write_talk_rejects_unknown_section(seeded_store):
    with pytest.raises(CfpError) as info:
        talks.write_talk(seeded_store, None, {"title": "X", "sections": {"Bogus": "no"}}, today=TODAY)
    assert "Bogus" in str(info.value)


def test_slug_collision_appends_suffix(seeded_store):
    first = talks.write_talk(seeded_store, None, {"title": "Same Title"}, today=TODAY)
    second = talks.write_talk(seeded_store, None, {"title": "Same Title"}, today=TODAY)
    assert first["id"] == "same-title" and second["id"] == "same-title-2"


def test_slug_collision_check_ignores_case(seeded_store):
    # On a case-insensitive file system "foo.md" and "Foo.md" are the same file,
    # so a hand-created "Foo.md" must not be clobbered by the slug "foo".
    existing = seeded_store / "talks" / "Foo.md"
    store.save(existing, {"id": "Foo", "title": "Hand made"}, "## Problem\n\nKeep me.\n")
    before = existing.read_bytes()
    result = talks.write_talk(seeded_store, None, {"title": "Foo"}, today=TODAY)
    assert result["id"] == "foo-2" and result["created"] is True
    assert existing.read_bytes() == before
    assert store.existing_ids(seeded_store, "talks") == {"foo", "foo-2"}
    assert store.existing_ids(seeded_store, "nothing-here") == set()


def test_complete_lists_empty_sections_and_personas(seeded_store):
    talks.write_talk(seeded_store, "t1", {"title": "T1", "sections": {"Problem": "P"}}, today=TODAY)
    result = talks.complete_talk(seeded_store, "t1")
    assert result["complete"] is False
    assert result["missing"] == ["Contribution", "Takeaways", "What is new", "Story notes"]
    assert result["missing_meta"] == ["personas"]
    talks.write_talk(
        seeded_store,
        "t1",
        {
            "personas": ["SREs"],
            "sections": {"Contribution": "C", "Takeaways": "- t", "What is new": "N", "Story notes": "S"},
        },
        today=TODAY,
    )
    assert talks.complete_talk(seeded_store, "t1") == {"complete": True, "missing": [], "missing_meta": []}


def test_write_talk_uses_id_from_json(seeded_store):
    first = talks.write_talk(seeded_store, None, {"id": "fixed-id", "title": "Same Title"}, today=TODAY)
    second = talks.write_talk(seeded_store, None, {"id": "fixed-id", "title": "Same Title"}, today=TODAY)
    assert first["id"] == "fixed-id" and first["created"] is True
    assert second["id"] == "fixed-id" and second["created"] is False


def test_list_talks_includes_proposals_and_last_presented(seeded_store):
    talks.write_talk(
        seeded_store,
        "t1",
        {
            "title": "T1",
            "outings": [
                {"event": "KubeCon EU 2025", "family": "kubecon", "date": "2025-04-02", "link": "", "kind": "presented"},
                {"event": "Other", "family": "", "date": "2026-02-01", "link": "", "kind": "submitted"},
                {"event": "KubeCon NA 2025", "family": "kubecon", "date": "2025-11-11", "link": "", "kind": "presented"},
            ],
        },
        today=TODAY,
    )
    talks.write_talk(seeded_store, "t2", {"title": "T2", "status": "retired"}, today=TODAY)
    store.save(store.proposal_path(seeded_store, "kubecon-eu-2027--t1"), {"id": "kubecon-eu-2027--t1", "talk": "t1", "status": "draft"}, "")
    store.save(store.proposal_path(seeded_store, "kubecon-na-2026--t1"), {"id": "kubecon-na-2026--t1", "talk": "t1", "status": "rejected"}, "")
    (seeded_store / "talks" / "broken.md").write_text("---\nid: broken\n", encoding="utf-8")

    listing, problems = talks.list_talks(seeded_store)
    assert len(problems) == 1
    by_id = {t["id"]: t for t in listing}
    assert by_id["t1"]["proposals"] == ["kubecon-eu-2027--t1", "kubecon-na-2026--t1"]
    assert by_id["t1"]["last_presented"] == "2025-11-11"
    assert by_id["t2"]["last_presented"] is None and by_id["t2"]["proposals"] == []
    active, _ = talks.list_talks(seeded_store, status="active")
    assert [t["id"] for t in active] == ["t1"]


def test_show_unknown_talk(seeded_store):
    with pytest.raises(CfpError):
        talks.show_talk(seeded_store, "nope")


def test_talk_cli(seeded_store, run_cli, write_json):
    written = run_cli("talk", "write", "--from-json", write_json({"title": "CLI Talk", "sections": {"Problem": "P"}}))
    assert written["id"] == "cli-talk" and written["created"] is True
    shown = run_cli("talk", "show", "--talk", "cli-talk")
    assert shown["sections"]["Problem"] == "P" and shown["title"] == "CLI Talk"
    complete = run_cli("talk", "complete", "--talk", "cli-talk")
    assert complete["complete"] is False and "Contribution" in complete["missing"]
    listing = run_cli("talk", "list")
    assert listing["talks"][0]["id"] == "cli-talk" and listing["problems"] == []
    updated = run_cli("talk", "write", "--talk", "cli-talk", "--from-json", write_json({"sections": {"Contribution": "C"}}))
    assert updated["created"] is False
