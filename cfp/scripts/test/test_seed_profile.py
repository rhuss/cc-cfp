"""The shipped KubeCon seed profile must validate and carry the documented values."""

from cfplib import frontmatter, profile
from conftest import SEED_DIR, TEMPLATES_DIR

EXPECTED_FIELDS = [
    "title", "abstract", "value_to_community", "audience_level", "track", "format", "case_study",
    "previously_presented", "cncf_oss_projects", "resources",
]
EXPECTED_RULE_KINDS = {
    "submission_limit", "repeat_within_months", "track_in_event", "speaker_count",
    "all_men_panel", "multi_company_panel", "vendor_pitch",
}


def test_seed_files_parse_and_are_approved():
    meta, body = frontmatter.load(SEED_DIR / "kubecon" / "profile.md")
    assert meta["id"] == "kubecon" and meta["approved"] is True
    assert meta["seed_version"] == "2026-10-11"
    assert "Drafting guidance" in frontmatter.sections(body)
    for event_id in ("kubecon-eu-2027", "kubecon-na-2026"):
        event, _ = frontmatter.load(SEED_DIR / "kubecon" / "events" / f"{event_id}.md")
        assert event["id"] == event_id and event["profile"] == "kubecon" and event["approved"] is True


def test_seed_profile_validates_in_a_store(seeded_store):
    assert profile.validate(seeded_store, "kubecon") == []
    assert profile.validate(seeded_store, "kubecon", "kubecon-eu-2027") == []
    assert profile.validate(seeded_store, "kubecon", "kubecon-na-2026") == []


def test_seed_profile_content(seeded_store):
    prof = profile.load_profile(seeded_store, "kubecon")
    assert [f["id"] for f in prof["fields"]] == EXPECTED_FIELDS
    assert [t["id"] for t in prof["session_types"]] == ["session", "panel", "lightning", "tutorial", "poster"]
    assert prof["submission_limit"] == 3
    assert prof["bio_limit"] == 500 and prof["bio_limit_status"] == "screenshot"
    assert {r["kind"] for r in prof["rules"]} == EXPECTED_RULE_KINDS
    assert all(r["source"].startswith("https://") for r in prof["rules"])
    rubric = prof["rubric"]
    assert [c["id"] for c in rubric["criteria"]] == ["content", "originality", "relevance", "speaker", "not_product_pitch"]
    assert rubric["scale_max"] == 5 and rubric["pass_average"] == 4.0 and rubric["pass_min_criterion"] == 3.0
    assert len(prof["rejection_reasons"]) >= 6


def test_seed_limits_and_their_status(seeded_store):
    prof = profile.load_profile(seeded_store, "kubecon")
    by_id = {f["id"]: f for f in prof["fields"]}
    limited = [f for f in prof["fields"] if f.get("limit") is not None]
    assert {f["id"]: f["limit"] for f in limited} == {"title": 75, "abstract": 1000}
    assert by_id["title"]["limit_status"] == "unverified"
    assert by_id["abstract"]["limit_status"] == "screenshot"
    assert all(f["limit_status"] in {"unverified", "screenshot"} for f in prof["fields"] if "limit_status" in f)
    value = by_id["value_to_community"]
    assert value["audience"] == "reviewer" and value["kind"] == "longtext" and value["limit"] is None
    assert by_id["resources"]["kind"] == "longtext"


def test_seed_events(seeded_store):
    eu = profile.load_effective(seeded_store, "kubecon", "kubecon-eu-2027")
    na = profile.load_effective(seeded_store, "kubecon", "kubecon-na-2026")
    assert len(eu["tracks"]) == 13 and len(na["tracks"]) == 11
    assert next(t for t in eu["session_types"] if t["id"] == "tutorial")["duration_min"] == 80
    assert next(t for t in na["session_types"] if t["id"] == "tutorial")["duration_min"] == 75
    assert eu["event"]["cfp_close"] == "2026-10-11" and na["event"]["cfp_close"] == "2026-05-31"
    assert eu["event"]["location"] == "Barcelona" and na["event"]["location"] == "Salt Lake City"
    assert eu["submission_limit"] == 3 and na["submission_limit"] == 3
    assert "Platform Engineering: DevEx + IDPs" in eu["tracks"]
    assert "AI Inference + Infrastructure" in eu["tracks"]


def test_seed_example_present(seeded_store):
    examples, _ = profile.list_examples(seeded_store, "kubecon")
    assert [e["id"] for e in examples] == ["lf-sample-container-runtime"]
    assert examples[0]["origin"] == "official-sample" and examples[0]["benefits"]


def test_profile_template_documents_bio_on_form():
    meta, _ = frontmatter.load(TEMPLATES_DIR / "profile.md")
    assert meta["bio_on_form"] is True
    assert list(meta).index("bio_on_form") < list(meta).index("bio_limit")
