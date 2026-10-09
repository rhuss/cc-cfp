"""Tests for bio variations and speaker resources (cfplib.bios)."""

import pytest

from cfplib import CfpError, bios, store

TODAY = "2026-10-09"


def test_write_bio_recounts_chars_and_round_trips(seeded_store):
    text = "  Roland Huss is a software engineer who works on Kubernetes.\r\nHe speaks at conferences.  \n"
    result = bios.write_bio(seeded_store, "short-cloud-native", "cloud-native", 450, text, today=TODAY)
    expected = len("Roland Huss is a software engineer who works on Kubernetes.\nHe speaks at conferences.")
    assert result["chars"] == expected
    assert result["path"] == str(store.bio_path(seeded_store, "short-cloud-native"))
    shown = bios.show_bio(seeded_store, "short-cloud-native")
    assert shown["name"] == "short-cloud-native"
    assert shown["emphasis"] == "cloud-native"
    assert shown["target_length"] == 450
    assert shown["chars"] == expected
    assert shown["updated"] == TODAY
    assert shown["text"].startswith("Roland Huss") and shown["text"].endswith("conferences.")


def test_write_bio_updates_existing(seeded_store):
    bios.write_bio(seeded_store, "b", "ai", 800, "First.", today="2026-01-01")
    bios.write_bio(seeded_store, "b", None, None, "Second text.", today=TODAY)
    shown = bios.show_bio(seeded_store, "b")
    assert shown["text"] == "Second text." and shown["chars"] == 12
    assert shown["emphasis"] == "ai" and shown["target_length"] == 800
    assert shown["updated"] == TODAY


def test_list_bios(seeded_store):
    bios.write_bio(seeded_store, "long-ai", "ai", 800, "x" * 700, today=TODAY)
    bios.write_bio(seeded_store, "short", "general", 400, "y" * 300, today=TODAY)
    (seeded_store / "bios" / "broken.md").write_text("no front matter", encoding="utf-8")
    listing, problems = bios.list_bios(seeded_store)
    assert [b["name"] for b in listing] == ["long-ai", "short"]
    assert listing[0] == {"name": "long-ai", "emphasis": "ai", "target_length": 800, "chars": 700, "updated": TODAY}
    assert len(problems) == 1 and problems[0]["path"].endswith("broken.md")


def test_show_bio_recounts_after_manual_edit(seeded_store):
    bios.write_bio(seeded_store, "b", "ai", 800, "Short.", today=TODAY)
    path = store.bio_path(seeded_store, "b")
    path.write_text(path.read_text().replace("Short.", "A much longer hand-edited bio text."), encoding="utf-8")
    assert bios.show_bio(seeded_store, "b")["chars"] == len("A much longer hand-edited bio text.")
    assert bios.list_bios(seeded_store)[0][0]["chars"] == len("A much longer hand-edited bio text.")


def test_delete_bio(seeded_store):
    bios.write_bio(seeded_store, "b", "ai", 800, "Text.", today=TODAY)
    result = bios.delete_bio(seeded_store, "b")
    assert result["deleted"].endswith("b.md")
    assert not store.bio_path(seeded_store, "b").exists()
    with pytest.raises(CfpError):
        bios.delete_bio(seeded_store, "b")
    with pytest.raises(CfpError):
        bios.show_bio(seeded_store, "b")


def test_write_resource_generates_id_from_title(seeded_store):
    result = bios.write_resource(
        seeded_store,
        {"type": "recording", "title": "KubeCon EU 2025 session recording", "link": "https://youtu.be/abc", "date": "2025-04-02"},
    )
    assert result["id"] == "kubecon-eu-2025-session-recording"
    assert result["path"].endswith("kubecon-eu-2025-session-recording.md")
    meta, _ = store.load(store.resource_path(seeded_store, result["id"]))
    assert meta["type"] == "recording" and meta["link"] == "https://youtu.be/abc" and meta["date"] == "2025-04-02"
    assert meta["notes"] == ""
    again = bios.write_resource(seeded_store, {"type": "blog", "title": "KubeCon EU 2025 session recording", "link": "https://x"})
    assert again["id"] == "kubecon-eu-2025-session-recording-2"
    explicit = bios.write_resource(seeded_store, {"id": "my-repo", "type": "repository", "title": "Repo", "link": "https://g"})
    assert explicit["id"] == "my-repo"
    updated = bios.write_resource(seeded_store, {"id": "my-repo", "type": "repository", "title": "Repo renamed", "link": "https://g"})
    assert updated["id"] == "my-repo"
    assert store.load(store.resource_path(seeded_store, "my-repo"))[0]["title"] == "Repo renamed"


def test_write_resource_slug_collision_ignores_case(seeded_store):
    existing = seeded_store / "resources" / "Rec.md"
    store.save(existing, {"id": "Rec", "type": "blog", "title": "Hand made", "link": "https://h"}, "")
    before = existing.read_bytes()
    result = bios.write_resource(seeded_store, {"type": "recording", "title": "Rec", "link": "https://r"})
    assert result["id"] == "rec-2"
    assert existing.read_bytes() == before


def test_write_resource_validates(seeded_store):
    with pytest.raises(CfpError):
        bios.write_resource(seeded_store, {"type": "recording", "link": "https://x"})
    with pytest.raises(CfpError):
        bios.write_resource(seeded_store, {"type": "video", "title": "T", "link": "https://x"})
    with pytest.raises(CfpError):
        bios.write_resource(seeded_store, {"type": "recording", "title": "T"})


def test_list_resources_filtered_by_type(seeded_store):
    bios.write_resource(seeded_store, {"type": "recording", "title": "Rec", "link": "https://r"})
    bios.write_resource(seeded_store, {"type": "repository", "title": "Repo", "link": "https://g"})
    bios.write_resource(seeded_store, {"type": "blog", "title": "Post", "link": "https://b", "date": "2026-01-01"})
    listing, problems = bios.list_resources(seeded_store)
    assert problems == []
    assert [r["id"] for r in listing] == ["post", "rec", "repo"]
    assert listing[1] == {"id": "rec", "type": "recording", "title": "Rec", "link": "https://r", "date": None, "notes": ""}
    only, _ = bios.list_resources(seeded_store, kind="recording")
    assert [r["id"] for r in only] == ["rec"]


def test_delete_resource(seeded_store):
    bios.write_resource(seeded_store, {"type": "recording", "title": "Rec", "link": "https://r"})
    assert bios.delete_resource(seeded_store, "rec")["deleted"].endswith("rec.md")
    with pytest.raises(CfpError):
        bios.delete_resource(seeded_store, "rec")
