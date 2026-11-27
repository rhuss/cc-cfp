"""Tests for character counting and limit evaluation (cfplib.counts)."""

import pytest

from cfplib import bios, counts, frontmatter, proposals, store, talks, text as textutil

TODAY = "2026-10-09"
EVENT = "kubecon-eu-2027"


@pytest.fixture
def pid(seeded_store):
    talks.write_talk(seeded_store, "t", {"title": "T"}, today=TODAY)
    return proposals.create(seeded_store, "t", "kubecon", EVENT, "session", today=TODAY)["id"]


def test_count_chars_normalizes_and_counts_code_points():
    assert textutil.count_chars("  hello  ") == 5
    assert textutil.count_chars("a\r\nb") == 3
    assert textutil.count_chars("straße") == 6
    assert textutil.count_chars("ok \U0001F680") == 4
    assert textutil.count_chars("") == 0
    assert textutil.count_chars(None) == 0


def test_count_proposal_statuses(seeded_store, pid):
    s = seeded_store
    proposals.set_field(s, pid, "title", "x" * 76, today=TODAY)
    proposals.set_field(s, pid, "abstract", "An abstract.", today=TODAY)
    proposals.set_field(s, pid, "cncf_oss_projects", "Kubernetes", today=TODAY)
    bios.write_bio(s, "b", "ai", 500, "y" * 501, today=TODAY)
    proposals.set_meta(s, pid, bio="b", today=TODAY)

    result = counts.count_proposal(s, pid)
    by_id = {f["id"]: f for f in result["fields"]}
    assert [f["id"] for f in result["fields"]] == [
        "title", "abstract", "value_to_community", "audience_level", "track", "format", "case_study",
        "previously_presented", "cncf_oss_projects", "resources",
    ]
    assert by_id["title"] == {"id": "title", "label": "Session Title", "required": True, "chars": 76, "limit": 75, "limit_status": "unverified", "status": "over", "drafted": True}
    assert by_id["abstract"]["chars"] == 12 and by_id["abstract"]["status"] == "ok"
    assert by_id["cncf_oss_projects"]["status"] == "no-limit" and by_id["cncf_oss_projects"]["limit"] is None
    assert by_id["value_to_community"]["chars"] == 0 and by_id["value_to_community"]["drafted"] is False and by_id["value_to_community"]["status"] == "no-limit"
    assert by_id["resources"]["required"] is False
    assert result["over"] == ["title"]
    assert result["missing_required"] == ["value_to_community", "audience_level", "track", "format", "case_study", "previously_presented"]
    assert result["bio"] == {"chars": 501, "limit": 500, "limit_status": "screenshot", "status": "over", "on_form": True, "drafted": True}
    assert result["proposal"] == pid


def test_count_at_limit_is_not_over(seeded_store, pid):
    s = seeded_store
    proposals.set_field(s, pid, "title", "x" * 75, today=TODAY)
    bios.write_bio(s, "b", "ai", 500, "y" * 500, today=TODAY)
    proposals.set_meta(s, pid, bio="b", today=TODAY)
    result = counts.count_proposal(s, pid)
    title = next(f for f in result["fields"] if f["id"] == "title")
    assert title["chars"] == 75 and title["status"] == "unverified"
    assert result["bio"]["chars"] == 500 and result["bio"]["status"] == "ok"
    assert result["over"] == []


def test_count_tolerates_non_integer_limit_from_hand_edit(seeded_store, pid):
    s = seeded_store
    path = store.profile_path(s, "kubecon")
    meta, body = frontmatter.load(path)
    for field in meta["fields"]:
        if field["id"] == "title":
            field["limit"] = "about 75"
    meta["bio_limit"] = "n/a"
    frontmatter.save(path, meta, body)
    proposals.set_field(s, pid, "title", "x" * 80, today=TODAY)
    result = counts.count_proposal(s, pid)
    title = next(f for f in result["fields"] if f["id"] == "title")
    assert title["limit"] is None and title["status"] == "no-limit"
    assert result["bio"]["limit"] is None and result["over"] == []


def test_count_ok_when_limit_verified(seeded_store, pid):
    s = seeded_store
    path = store.profile_path(s, "kubecon")
    meta, body = frontmatter.load(path)
    for field in meta["fields"]:
        if field["id"] == "title":
            field["limit_status"] = "page"
    meta["bio_limit_status"] = "screenshot"
    frontmatter.save(path, meta, body)
    proposals.set_field(s, pid, "title", "Short", today=TODAY)
    proposals.set_bio_text(s, pid, "Bio.", today=TODAY)
    result = counts.count_proposal(s, pid)
    assert next(f for f in result["fields"] if f["id"] == "title")["status"] == "ok"
    assert result["bio"]["status"] == "ok"
    assert result["over"] == []


def test_count_bio_without_limit(seeded_store, pid):
    s = seeded_store
    path = store.profile_path(s, "kubecon")
    meta, body = frontmatter.load(path)
    meta["bio_limit"] = None
    frontmatter.save(path, meta, body)
    result = counts.count_proposal(s, pid)
    assert result["bio"]["status"] == "no-limit" and result["bio"]["drafted"] is False


def test_count_bio_not_on_form(seeded_store, pid):
    s = seeded_store
    bios.write_bio(s, "b", "ai", 500, "y" * 501, today=TODAY)
    proposals.set_meta(s, pid, bio="b", today=TODAY)
    path = store.profile_path(s, "kubecon")
    meta, body = frontmatter.load(path)
    meta["bio_on_form"] = False
    frontmatter.save(path, meta, body)
    result = counts.count_proposal(s, pid)
    # a stored snapshot is counted but never measured against a limit the form does not have
    assert result["bio"] == {"chars": 501, "limit": None, "limit_status": None, "status": "not-on-form", "on_form": False, "drafted": True}
    assert result["over"] == []


def test_count_cli(seeded_store, pid, run_cli):
    result = run_cli("count", "--proposal", pid)
    assert result["over"] == [] and "title" in result["missing_required"]
    assert run_cli("count", "--proposal", "nope", expect_ok=False).code == 1
