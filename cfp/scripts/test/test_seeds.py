"""Tests for comparing shipped seed profiles with the store and updating outdated copies (cfplib.seeds)."""

import shutil

import pytest

from cfplib import CfpError, frontmatter, profile, seeds, store
from conftest import SEED_DIR

SHIPPED = frontmatter.load(SEED_DIR / "kubecon" / "profile.md")[0]["seed_version"]
OLD = "2026-10-09"
EU = "events/kubecon-eu-2027.md"
NA = "events/kubecon-na-2026.md"
EXAMPLE = "examples/lf-sample-container-runtime.md"


def edit(path, change):
    meta, body = frontmatter.load(path)
    change(meta)
    frontmatter.save(path, meta, body)


def age_store_profile(s, version=OLD):
    """Make the store copy look like an older seed: older version and one stale limit."""

    def change(meta):
        meta["seed_version"] = version
        for field in meta["fields"]:
            if field["id"] == "abstract":
                field["limit"] = 1300

    edit(store.profile_path(s, "kubecon"), change)


def kubecon(result):
    return {seed["profile"]: seed for seed in result}["kubecon"]


def diverge(s):
    """An outdated profile, one hand-edited shipped event, one deleted shipped example."""
    age_store_profile(s)
    edit(store.event_path(s, "kubecon", "kubecon-eu-2027"), lambda meta: meta.update(tracks=["Only Track"], approved=False))
    store.example_path(s, "kubecon", "lf-sample-container-runtime").unlink()


def test_status_is_current_right_after_init(seeded_store):
    info = kubecon(seeds.status(seeded_store, SEED_DIR))
    assert info == {"profile": "kubecon", "state": "current", "store_version": SHIPPED, "seed_version": SHIPPED, "files": []}


def test_status_local_newer_missing_and_unreadable(seeded_store, tmp_path):
    s = seeded_store
    path = store.profile_path(s, "kubecon")
    edit(path, lambda meta: meta.update(seed_version=""))
    info = kubecon(seeds.status(s, SEED_DIR))
    assert info["state"] == "local" and info["store_version"] == "" and info["files"] == []
    edit(path, lambda meta: meta.update(seed_version="2099-01-01"))
    assert kubecon(seeds.status(s, SEED_DIR))["state"] == "newer"
    path.write_text("---\nid: kubecon\n  bad: indent\n---\n")
    info = kubecon(seeds.status(s, SEED_DIR))
    assert info["state"] == "unreadable" and str(path) in info["error"]
    shutil.rmtree(store.profile_dir(s, "kubecon"))
    info = kubecon(seeds.status(s, SEED_DIR))
    assert info["state"] == "missing" and info["store_version"] is None
    with pytest.raises(CfpError, match="seed directory not found"):
        seeds.status(s, tmp_path / "nope")


def test_status_outdated_lists_shipped_files_with_diffs(seeded_store):
    s = seeded_store
    diverge(s)
    profile.approve(s, "kubecon", approved=False)
    info = kubecon(seeds.status(s, SEED_DIR))
    assert info["state"] == "outdated" and info["store_version"] == OLD and info["seed_version"] == SHIPPED
    files = {entry["path"]: entry for entry in info["files"]}
    assert list(files) == ["profile.md", EU, NA, EXAMPLE]

    diff = files["profile.md"]["diff"]
    assert files["profile.md"]["state"] == "changed"
    assert diff.startswith("--- store/profile.md\n+++ shipped/profile.md\n")
    changed = [line for line in diff.splitlines() if line[:1] in "+-" and not line.startswith(("---", "+++"))]
    # only what really differs: no noise from quoting, key order, or the approval flag
    assert sorted(changed) == sorted([f"-seed_version: {OLD}", f"+seed_version: {SHIPPED}", "-    limit: 1300", "+    limit: 1000"])

    assert files[EU]["state"] == "changed" and "+  - Agentic AI" in files[EU]["diff"] and "-  - Only Track" in files[EU]["diff"]
    assert "approved" not in files[EU]["diff"]
    assert files[NA] == {"path": NA, "state": "same"}
    assert files[EXAMPLE] == {"path": EXAMPLE, "state": "missing"}


def test_update_replaces_the_profile_only_by_default_and_keeps_its_approval(seeded_store):
    s = seeded_store
    diverge(s)
    profile.approve(s, "kubecon", approved=False)
    result = seeds.update(s, SEED_DIR, "kubecon")
    assert result == {
        "profile": "kubecon", "from_version": OLD, "to_version": SHIPPED,
        "updated": ["profile.md"], "added": [], "skipped": [EU, EXAMPLE],
    }
    prof = profile.load_profile(s, "kubecon")
    assert prof["seed_version"] == SHIPPED and prof["approved"] is False
    assert next(f for f in prof["fields"] if f["id"] == "abstract")["limit"] == 1000
    assert profile.load_event(s, "kubecon", "kubecon-eu-2027")["tracks"] == ["Only Track"]
    assert not store.example_path(s, "kubecon", "lf-sample-container-runtime").exists()
    assert kubecon(seeds.status(s, SEED_DIR))["state"] == "current"


def test_update_with_chosen_files_keeps_event_approval_and_adds_missing_files(seeded_store):
    s = seeded_store
    diverge(s)
    result = seeds.update(s, SEED_DIR, "kubecon", files=[EXAMPLE, EU, NA, "profile.md"])
    # shipped order, an unchanged file is not rewritten, profile.md is never listed twice
    assert result["updated"] == ["profile.md", EU] and result["added"] == [EXAMPLE] and result["skipped"] == []
    event = profile.load_event(s, "kubecon", "kubecon-eu-2027")
    assert len(event["tracks"]) == 13 and event["approved"] is False
    assert profile.load_profile(s, "kubecon")["approved"] is True
    assert store.example_path(s, "kubecon", "lf-sample-container-runtime").is_file()
    assert profile.validate(s, "kubecon", "kubecon-eu-2027") == []


def test_update_all_takes_every_open_file(seeded_store):
    s = seeded_store
    diverge(s)
    result = seeds.update(s, SEED_DIR, "kubecon", all_files=True)
    assert result["updated"] == ["profile.md", EU] and result["added"] == [EXAMPLE] and result["skipped"] == []


def test_update_refuses_without_writing(seeded_store):
    s = seeded_store
    with pytest.raises(CfpError, match="not outdated"):
        seeds.update(s, SEED_DIR, "kubecon")
    age_store_profile(s)
    for bad in ("events/nope.md", "../../config.md", "/etc/hosts"):
        with pytest.raises(CfpError, match="not a file of the shipped profile"):
            seeds.update(s, SEED_DIR, "kubecon", files=[bad])
    with pytest.raises(CfpError, match="no shipped profile"):
        seeds.update(s, SEED_DIR, "nope")
    with pytest.raises(CfpError, match="invalid profile id"):
        seeds.update(s, SEED_DIR, "../kubecon")
    assert profile.load_profile(s, "kubecon")["seed_version"] == OLD


def test_files_that_only_the_store_has_are_never_touched(seeded_store):
    s = seeded_store
    age_store_profile(s)
    own = store.event_path(s, "kubecon", "kubecon-india-2027")
    frontmatter.save(own, {"id": "kubecon-india-2027", "profile": "kubecon", "approved": True, "tracks": ["AI"]}, "## Notes\n")
    before = own.read_text()
    assert "events/kubecon-india-2027.md" not in [entry["path"] for entry in kubecon(seeds.status(s, SEED_DIR))["files"]]
    seeds.update(s, SEED_DIR, "kubecon", all_files=True)
    assert own.read_text() == before


def test_seed_cli(seeded_store, run_cli):
    status = run_cli("profile", "seed-status", "--seed-dir", SEED_DIR)
    assert [seed["profile"] for seed in status["seeds"]] == ["kubecon"] and status["seeds"][0]["state"] == "current"
    refused = run_cli("profile", "seed-update", "--profile", "kubecon", "--seed-dir", SEED_DIR, expect_ok=False)
    assert refused.code == 1 and "not outdated" in refused["error"]

    diverge(seeded_store)
    status = run_cli("profile", "seed-status", "--seed-dir", SEED_DIR)
    assert status["seeds"][0]["state"] == "outdated" and len(status["seeds"][0]["files"]) == 4
    both = run_cli("profile", "seed-update", "--profile", "kubecon", "--seed-dir", SEED_DIR, "--all", "--files", EU, expect_ok=False)
    assert both.code == 2
    updated = run_cli("profile", "seed-update", "--profile", "kubecon", "--seed-dir", SEED_DIR, "--files", f"{EU},{EXAMPLE}")
    assert updated["updated"] == ["profile.md", EU] and updated["added"] == [EXAMPLE] and updated["to_version"] == SHIPPED
    assert run_cli("profile", "seed-status", "--seed-dir", SEED_DIR)["seeds"][0]["state"] == "current"
