"""Tests for profile and event override handling (cfplib.profile)."""

import pytest

from cfplib import CfpError, frontmatter, profile, store


def test_load_seed_profile_and_event(seeded_store):
    prof = profile.load_profile(seeded_store, "kubecon")
    assert prof["id"] == "kubecon"
    assert prof["approved"] is True
    assert len(prof["session_types"]) == 5
    event = profile.load_event(seeded_store, "kubecon", "kubecon-eu-2027")
    assert event["id"] == "kubecon-eu-2027"
    assert len(event["tracks"]) == 13
    with pytest.raises(CfpError):
        profile.load_profile(seeded_store, "nope")
    with pytest.raises(CfpError):
        profile.load_event(seeded_store, "kubecon", "kubecon-india-2026")


def test_effective_merge_with_seed_event(seeded_store):
    prof = profile.load_profile(seeded_store, "kubecon")
    event = profile.load_event(seeded_store, "kubecon", "kubecon-eu-2027")
    eff = profile.effective(prof, event)
    tutorial = next(t for t in eff["session_types"] if t["id"] == "tutorial")
    assert tutorial["duration_min"] == 80
    assert tutorial["max_speakers"] == 5  # untouched keys survive
    assert eff["submission_limit"] == 3
    assert len(eff["tracks"]) == 13
    track_field = next(f for f in eff["fields"] if f["id"] == "track")
    assert track_field["options"] == eff["tracks"]
    assert eff["approved"] is True
    assert eff["profile"]["id"] == "kubecon"
    assert eff["event"]["id"] == "kubecon-eu-2027"
    assert eff["bio_limit"] == 500 and eff["bio_limit_status"] == "screenshot"
    assert "value proposition" in eff["drafting_guidance"]
    assert "Seeded from" in eff["notes"]


def test_relevance_field_id_rules():
    def field(field_id, audience="reviewer", kind="longtext"):
        return {"id": field_id, "audience": audience, "kind": kind}

    kubecon_like = [
        field("title", "public", "text"), field("abstract", "public"), field("value_to_community"),
        field("previously_presented"), field("resources"),
    ]
    assert profile.relevance_field_id(kubecon_like) == "value_to_community"
    # an older form's benefits field wins wherever it sits
    assert profile.relevance_field_id([field("notes"), field("benefits")]) == "benefits"
    # fields with their own drafting rule are never the relevance field
    assert profile.relevance_field_id([field("previously_presented"), field("resources"), field("why_this_talk")]) == "why_this_talk"
    assert profile.relevance_field_id([field("resources", kind="resources"), field("previously_presented")]) is None
    # public fields and short text fields do not qualify
    assert profile.relevance_field_id([field("abstract", "public"), field("notes", kind="text")]) is None
    assert profile.relevance_field_id([]) is None
    assert profile.relevance_field_id(None) is None


def test_effective_names_the_relevance_field(seeded_store):
    eff = profile.load_effective(seeded_store, "kubecon", "kubecon-eu-2027")
    assert eff["relevance_field"] == "value_to_community"
    # an event override that adds an older benefits field changes the answer for that edition only
    prof = profile.load_profile(seeded_store, "kubecon")
    event = {"id": "x", "field_overrides": [{"id": "benefits", "label": "Benefits", "kind": "longtext", "audience": "reviewer"}]}
    assert profile.effective(prof, event)["relevance_field"] == "benefits"
    assert profile.effective(prof, None)["relevance_field"] == "value_to_community"


def test_effective_without_event(seeded_store):
    prof = profile.load_profile(seeded_store, "kubecon")
    eff = profile.effective(prof, None)
    assert eff["event"] is None
    assert eff["tracks"] == []
    assert eff["submission_limit"] == 3


def test_effective_override_replace_remove_and_field_override(seeded_store):
    prof = profile.load_profile(seeded_store, "kubecon")
    event = {
        "id": "x",
        "profile": "kubecon",
        "approved": False,
        "tracks": ["A"],
        "submission_limit": 2,
        "session_type_overrides": [
            {"id": "poster", "remove": True},
            {"id": "lightning", "duration_min": 10},
            {"id": "workshop", "name": "Workshop", "duration_min": 120, "min_speakers": 1, "max_speakers": 3},
        ],
        "field_overrides": [
            {"id": "title", "limit": 60, "limit_status": "screenshot", "source": "screenshot:form.png"},
            {"id": "extra", "label": "Extra", "kind": "text", "required": False},
        ],
    }
    eff = profile.effective(prof, event)
    ids = [t["id"] for t in eff["session_types"]]
    assert "poster" not in ids
    assert ids[-1] == "workshop"
    assert next(t for t in eff["session_types"] if t["id"] == "lightning")["duration_min"] == 10
    assert eff["submission_limit"] == 2
    title = next(f for f in eff["fields"] if f["id"] == "title")
    assert title["limit"] == 60 and title["limit_status"] == "screenshot"
    assert title["label"] == "Session Title"
    assert eff["fields"][-1]["id"] == "extra"
    assert eff["approved"] is False


def test_validate_seed_profile_is_clean(seeded_store):
    assert profile.validate(seeded_store, "kubecon") == []
    assert profile.validate(seeded_store, "kubecon", "kubecon-eu-2027") == []
    assert profile.validate(seeded_store, "kubecon", "kubecon-na-2026") == []


def test_validate_reports_problems(seeded_store):
    path = store.profile_path(seeded_store, "kubecon")
    meta, body = frontmatter.load(path)
    meta["fields"].append(dict(meta["fields"][0]))  # duplicate id
    meta["rules"][0]["kind"] = "bogus"
    meta["rubric"]["criteria"] = []
    meta["session_types"].append({"id": "session"})
    frontmatter.save(path, meta, body)
    problems = profile.validate(seeded_store, "kubecon")
    text = "\n".join(problems)
    assert "duplicate field id" in text
    assert "unknown rule kind" in text
    assert "rubric" in text
    assert "duplicate session type id" in text


def test_validate_event_problems(seeded_store):
    path = store.event_path(seeded_store, "kubecon", "kubecon-eu-2027")
    meta, body = frontmatter.load(path)
    meta["profile"] = "other"
    meta["tracks"] = []
    meta["session_type_overrides"] = [{"id": "ghost", "duration_min": 5}]
    frontmatter.save(path, meta, body)
    problems = profile.validate(seeded_store, "kubecon", "kubecon-eu-2027")
    text = "\n".join(problems)
    assert "profile" in text
    assert "tracks" in text


def test_approval_checks(seeded_store):
    assert profile.is_approved(seeded_store, "kubecon", "kubecon-eu-2027") == (True, [])
    profile.approve(seeded_store, "kubecon", event_id="kubecon-eu-2027", approved=False)
    ok, reasons = profile.is_approved(seeded_store, "kubecon", "kubecon-eu-2027")
    assert ok is False and "kubecon-eu-2027" in reasons[0]
    profile.approve(seeded_store, "kubecon", approved=False)
    ok, reasons = profile.is_approved(seeded_store, "kubecon")
    assert ok is False and "kubecon" in reasons[0]
    result = profile.approve(seeded_store, "kubecon", approved=True)
    assert result["approved"] is True
    assert profile.load_profile(seeded_store, "kubecon")["approved"] is True


def test_write_profile_and_event_from_json(tmp_store, tmp_home):
    from cfplib import config

    config.init_store(tmp_store, {"speaker_name": "A"}, seed_dir=None)
    data = {
        "name": "Example Conf",
        "platform": "pretalx",
        "session_types": [{"id": "talk", "name": "Talk", "duration_min": 40, "min_speakers": 1, "max_speakers": 2}],
        "fields": [
            {"id": "title", "label": "Title", "required": True, "kind": "text", "limit": 80, "limit_status": "page", "source": "https://x"},
        ],
        "rubric": {"scale_max": 5, "pass_average": 4.0, "pass_min_criterion": 3.0, "criteria": [{"id": "c", "name": "C", "description": ""}]},
        "rules": [],
        "body": {"Drafting guidance": "Be concrete.", "Notes": "none"},
    }
    path = profile.write_profile_from_json(tmp_store, "example", data)
    assert path == store.profile_path(tmp_store, "example")
    prof = profile.load_profile(tmp_store, "example")
    assert prof["id"] == "example"
    assert prof["approved"] is False
    assert prof["fields"][0]["limit"] == 80
    assert prof["drafting_guidance"] == "Be concrete."

    event_data = {"name": "Example Conf 2027", "tracks": ["T1"], "cfp_close": "2027-01-31", "approved": True}
    epath = profile.write_event_from_json(tmp_store, "example", "example-2027", event_data)
    assert epath == store.event_path(tmp_store, "example", "example-2027")
    event = profile.load_event(tmp_store, "example", "example-2027")
    assert event["approved"] is True and event["profile"] == "example"
    assert profile.validate(tmp_store, "example", "example-2027") == []

    # rewriting preserves keys not in the new JSON
    profile.write_profile_from_json(tmp_store, "example", {"name": "Renamed"})
    prof = profile.load_profile(tmp_store, "example")
    assert prof["name"] == "Renamed" and prof["platform"] == "pretalx"
    assert prof["drafting_guidance"] == "Be concrete."


def test_examples_add_and_list_newest_first(seeded_store):
    examples, problems = profile.list_examples(seeded_store, "kubecon")
    assert problems == []
    assert [e["id"] for e in examples] == ["lf-sample-container-runtime"]
    assert examples[0]["title"].startswith("OCI, CRI")
    assert examples[0]["benefits"]

    profile.add_example(
        seeded_store,
        "kubecon",
        {"title": "New Talk", "abstract": "A", "benefits": "B", "event": "kubecon-eu-2027", "year": 2027, "origin": "own-accepted", "proposal": "kubecon-eu-2027--new-talk"},
        today="2026-12-10",
    )
    profile.add_example(
        seeded_store,
        "kubecon",
        {"title": "Older Manual", "abstract": "A", "event": "KubeCon EU 2024", "year": 2024, "origin": "manual"},
        today="2026-11-01",
    )
    examples, _ = profile.list_examples(seeded_store, "kubecon")
    assert [e["id"] for e in examples] == ["kubecon-eu-2027--new-talk", "older-manual", "lf-sample-container-runtime"]
    assert profile.list_examples(seeded_store, "kubecon", limit=2)[0][1]["id"] == "older-manual"
    assert examples[1]["benefits"] == ""


def test_example_slug_collision_ignores_case(seeded_store):
    examples_dir = store.profile_dir(seeded_store, "kubecon") / "examples"
    existing = examples_dir / "New-Talk.md"
    store.save(existing, {"id": "New-Talk", "profile": "kubecon", "origin": "manual"}, "## Title\n\nHand made\n")
    before = existing.read_bytes()
    path = profile.add_example(seeded_store, "kubecon", {"title": "New Talk", "abstract": "A"}, today="2026-12-10")
    assert path.name == "new-talk-2.md"
    assert existing.read_bytes() == before


def test_profile_subdirectories_reject_path_traversal(seeded_store, tmp_path):
    outside = tmp_path / "outside" / "events"
    outside.mkdir(parents=True)
    (outside / "leaked.md").write_text("---\nid: leaked\n---\n", encoding="utf-8")
    with pytest.raises(CfpError, match="invalid profile id"):
        profile.list_events(seeded_store, "../../outside")
    with pytest.raises(CfpError, match="invalid profile id"):
        profile.list_examples(seeded_store, "../../outside")
    with pytest.raises(CfpError, match="invalid store directory"):
        store.list_dir(seeded_store, "../outside/events")


def test_days_to_close():
    assert profile.days_to_close({"cfp_close": "2026-10-11"}, "2026-10-09") == 2
    assert profile.days_to_close({"cfp_close": "2026-10-01"}, "2026-10-09") == -8
    assert profile.days_to_close({"cfp_close": None}, "2026-10-09") is None
    assert profile.days_to_close({}, "2026-10-09") is None


def test_list_profiles(seeded_store):
    listing, problems = profile.list_profiles(seeded_store, today="2026-10-09")
    assert problems == []
    assert listing[0]["id"] == "kubecon" and listing[0]["approved"] is True
    events = {e["id"]: e for e in listing[0]["events"]}
    assert events["kubecon-eu-2027"]["days_to_close"] == 2
    assert events["kubecon-na-2026"]["cfp_close"] == "2026-05-31"
