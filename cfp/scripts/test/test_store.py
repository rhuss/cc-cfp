"""Tests for slugs, path helpers, and generic load, save, list (cfplib.store)."""

import pytest

from cfplib import CfpError, frontmatter, store


def test_slugify_rules():
    assert store.slugify("What Broke When We Put Agents on the Platform") == "what-broke-when-we-put-agents-on-the-platform"
    assert store.slugify("  Ünïcode & Symbols: Test!  ") == "unicode-symbols-test"
    assert store.slugify("a--b__c") == "a-b-c"
    assert len(store.slugify("word " * 40)) <= 60
    assert not store.slugify("word " * 40).endswith("-")
    assert store.slugify("###") == "item"


def test_slugify_collisions():
    assert store.slugify("My Talk", existing={"my-talk"}) == "my-talk-2"
    assert store.slugify("My Talk", existing={"my-talk", "my-talk-2"}) == "my-talk-3"
    assert store.slugify("My Talk", existing=set()) == "my-talk"


def test_path_helpers(tmp_store):
    s = tmp_store
    assert store.talk_path(s, "t1") == s / "talks" / "t1.md"
    assert store.proposal_path(s, "ev--t1") == s / "proposals" / "ev--t1.md"
    assert store.bio_path(s, "short") == s / "bios" / "short.md"
    assert store.resource_path(s, "rec") == s / "resources" / "rec.md"
    assert store.profile_path(s, "kubecon") == s / "profiles" / "kubecon" / "profile.md"
    assert store.event_path(s, "kubecon", "eu") == s / "profiles" / "kubecon" / "events" / "eu.md"
    assert store.example_path(s, "kubecon", "ex") == s / "profiles" / "kubecon" / "examples" / "ex.md"
    assert store.proposal_id("kubecon-eu-2027", "my-talk") == "kubecon-eu-2027--my-talk"


def test_path_helpers_reject_unsafe_ids(tmp_store):
    with pytest.raises(CfpError):
        store.talk_path(tmp_store, "../escape")
    with pytest.raises(CfpError):
        store.bio_path(tmp_store, "")
    with pytest.raises(CfpError):
        store.event_path(tmp_store, "kubecon", "a/b")


def test_save_and_load_entities(seeded_store):
    s = seeded_store
    store.save(store.talk_path(s, "t1"), {"id": "t1", "title": "T"}, "## Problem\n\nP\n")
    store.save(store.bio_path(s, "b1"), {"name": "b1", "chars": 3}, "Bio\n")
    store.save(store.resource_path(s, "r1"), {"id": "r1", "type": "recording"}, "")
    store.save(store.proposal_path(s, "ev--t1"), {"id": "ev--t1", "status": "draft"}, "## Field: title\n\nX\n")

    meta, body = store.load(store.talk_path(s, "t1"))
    assert meta["title"] == "T"
    assert frontmatter.sections(body)["Problem"] == "P"
    assert store.load(store.bio_path(s, "b1"))[0]["chars"] == 3
    assert store.load(store.resource_path(s, "r1"))[0]["type"] == "recording"
    assert store.load(store.proposal_path(s, "ev--t1"))[0]["status"] == "draft"
    assert store.exists(store.talk_path(s, "t1"))
    assert not store.exists(store.talk_path(s, "nope"))


def test_load_missing_file_is_domain_error(tmp_store):
    with pytest.raises(CfpError) as info:
        store.load(tmp_store / "talks" / "missing.md")
    assert "missing.md" in str(info.value)


def test_list_dir_skips_invalid_files_and_reports_them(seeded_store):
    s = seeded_store
    store.save(store.talk_path(s, "good-a"), {"id": "good-a", "title": "A"}, "")
    store.save(store.talk_path(s, "good-b"), {"id": "good-b", "title": "B"}, "")
    (s / "talks" / "broken.md").write_text("---\nid: broken\ntitle: oops\n", encoding="utf-8")
    (s / "talks" / "notes.txt").write_text("ignored", encoding="utf-8")

    items, problems = store.list_dir(s, "talks")
    assert [meta["id"] for path, meta, body in items] == ["good-a", "good-b"]
    assert len(problems) == 1
    assert problems[0]["path"].endswith("broken.md")
    assert "closing" in problems[0]["error"]


def test_list_dir_missing_directory_is_empty(tmp_store):
    assert store.list_dir(tmp_store, "talks") == ([], [])


def test_list_profiles_dirs(seeded_store):
    ids = store.list_profile_ids(seeded_store)
    assert ids == ["kubecon"]
    events, problems = store.list_dir(seeded_store, "profiles/kubecon/events")
    assert sorted(meta["id"] for _, meta, _ in events) == ["kubecon-eu-2027", "kubecon-na-2026"]
    assert problems == []
