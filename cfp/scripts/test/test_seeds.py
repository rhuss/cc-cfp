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
    assert info == {
        "profile": "kubecon", "state": "current", "store_version": SHIPPED, "seed_version": SHIPPED, "files": [],
        "source": "plugin", "seed_dir": str(SEED_DIR / "kubecon"),
    }


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
        "source": "plugin", "warnings": [],
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


# ---------------------------------------------------------------- personal seed profiles (feature 002)

LATER = "2099-01-01"


def user_seed(user_dir, name, version=LATER, marker=None):
    """Copy the shipped kubecon seed to <user_dir>/<name> with its own id and seed_version."""
    target = user_dir / name
    shutil.copytree(SEED_DIR / "kubecon", target)

    def change(meta):
        meta["id"] = name
        if version is None:
            meta.pop("seed_version", None)
        else:
            meta["seed_version"] = version
        if marker:
            meta["name"] = marker

    edit(target / "profile.md", change)
    return target


def clash_warning(user_dir, suffix=""):
    return f"profile 'kubecon': using {user_dir / 'kubecon'} instead of the shipped {SEED_DIR / 'kubecon'}{suffix}"


NO_VERSION = "; it has no seed_version, so it will not replace an existing store copy"


def test_collect_plugin_only_and_missing_user_dir(tmp_path):
    expected = [{"name": "kubecon", "dir": SEED_DIR / "kubecon", "source": "plugin"}]
    assert seeds.collect(SEED_DIR) == (expected, [])
    assert seeds.collect(SEED_DIR, tmp_path / "missing") == (expected, [])
    with pytest.raises(CfpError, match="seed directory not found"):
        seeds.collect(tmp_path / "nope", tmp_path)


def test_collect_adds_user_profiles_and_skips_folders_without_profile(tmp_path):
    user_dir = tmp_path / "profiles"
    user_seed(user_dir, "acme-summit")
    (user_dir / "notes").mkdir()
    (user_dir / "notes" / "readme.md").write_text("no profile here")
    (user_dir / "stray.md").write_text("a file, not a folder")
    entries, warnings = seeds.collect(SEED_DIR, user_dir)
    assert entries == [
        {"name": "kubecon", "dir": SEED_DIR / "kubecon", "source": "plugin"},
        {"name": "acme-summit", "dir": user_dir / "acme-summit", "source": "user"},
    ]
    assert warnings == []


def test_collect_user_profile_replaces_shipped_one_with_warning(tmp_path):
    user_dir = tmp_path / "profiles"
    user_seed(user_dir, "kubecon")
    entries, warnings = seeds.collect(SEED_DIR, user_dir)
    assert entries == [{"name": "kubecon", "dir": user_dir / "kubecon", "source": "user"}]
    assert warnings == [clash_warning(user_dir)]


def test_collect_variant_without_seed_version_says_so(tmp_path):
    user_dir = tmp_path / "profiles"
    user_seed(user_dir, "kubecon", version=None)
    assert seeds.collect(SEED_DIR, user_dir)[1] == [clash_warning(user_dir, NO_VERSION)]


def test_status_report_marks_source_and_folder(seeded_store, tmp_path):
    user_dir = tmp_path / "profiles"
    user_seed(user_dir, "acme-summit")
    listing = seeds.status(seeded_store, SEED_DIR, user_dir)
    assert isinstance(listing, list)
    by_name = {seed["profile"]: seed for seed in listing}
    assert by_name["kubecon"]["source"] == "plugin" and by_name["kubecon"]["seed_dir"] == str(SEED_DIR / "kubecon")
    assert by_name["acme-summit"]["source"] == "user" and by_name["acme-summit"]["seed_dir"] == str(user_dir / "acme-summit")
    assert by_name["acme-summit"]["state"] == "missing"
    report, warnings = seeds.status_report(seeded_store, SEED_DIR, user_dir)
    assert report == listing and warnings == []


def test_variant_without_seed_version_never_replaces_versioned_copy(seeded_store, tmp_path):
    user_dir = tmp_path / "profiles"
    user_seed(user_dir, "kubecon", version=None)
    report, warnings = seeds.status_report(seeded_store, SEED_DIR, user_dir)
    info = kubecon(report)
    assert info["state"] == "current" and info["source"] == "user"
    assert warnings == [clash_warning(user_dir, NO_VERSION)]
    with pytest.raises(CfpError, match="not outdated"):
        seeds.update(seeded_store, SEED_DIR, "kubecon", user_dir=user_dir)


def test_user_seed_later_version_is_outdated_and_updates(seeded_store, tmp_path):
    user_dir = tmp_path / "profiles"
    user_seed(user_dir, "kubecon", version=LATER, marker="My KubeCon")
    info = kubecon(seeds.status(seeded_store, SEED_DIR, user_dir))
    assert info["state"] == "outdated" and info["store_version"] == SHIPPED and info["seed_version"] == LATER
    profile_diff = next(entry for entry in info["files"] if entry["path"] == "profile.md")["diff"]
    assert profile_diff.startswith("--- store/profile.md\n+++ user/profile.md\n")
    result = seeds.update(seeded_store, SEED_DIR, "kubecon", user_dir=user_dir)
    assert result["source"] == "user" and result["to_version"] == LATER
    assert result["warnings"] == [clash_warning(user_dir)]
    prof = profile.load_profile(seeded_store, "kubecon")
    assert prof["name"] == "My KubeCon" and prof["seed_version"] == LATER and prof["approved"] is True
    assert kubecon(seeds.status(seeded_store, SEED_DIR, user_dir))["state"] == "current"


def test_user_seed_lower_version_is_newer_and_refused(seeded_store, tmp_path):
    user_dir = tmp_path / "profiles"
    user_seed(user_dir, "kubecon", version="2000-01-01")
    info = kubecon(seeds.status(seeded_store, SEED_DIR, user_dir))
    assert info["state"] == "newer" and info["source"] == "user"
    with pytest.raises(CfpError, match="not outdated"):
        seeds.update(seeded_store, SEED_DIR, "kubecon", user_dir=user_dir)


def test_update_user_only_profile_and_unknown_name(seeded_store, tmp_path):
    from cfplib import config

    user_dir = tmp_path / "profiles"
    user_seed(user_dir, "acme-summit", version="2026-01-01")
    config.init_store(seeded_store, {"speaker_name": "A"}, seed_dir=SEED_DIR, user_seed_dir=user_dir)
    edit(user_dir / "acme-summit" / "profile.md", lambda meta: meta.update(seed_version="2026-06-01"))
    result = seeds.update(seeded_store, SEED_DIR, "acme-summit", user_dir=user_dir)
    assert result["source"] == "user" and result["from_version"] == "2026-01-01" and result["to_version"] == "2026-06-01"
    with pytest.raises(CfpError) as info:
        seeds.update(seeded_store, SEED_DIR, "nope", user_dir=user_dir)
    assert str(info.value) == f"no seed profile 'nope' in {SEED_DIR} or {user_dir}"


def test_update_refuses_to_write_through_a_symlinked_store_copy(seeded_store, tmp_path):
    user_dir = tmp_path / "profiles"
    user_seed(user_dir, "kubecon")
    outside = tmp_path / "outside.md"
    target = seeded_store / "profiles" / "kubecon" / "profile.md"
    outside.write_bytes(target.read_bytes())
    target.unlink()
    target.symlink_to(outside)
    before = outside.read_bytes()
    assert kubecon(seeds.status(seeded_store, SEED_DIR, user_dir))["state"] == "outdated"
    with pytest.raises(CfpError, match="contains symlinks"):
        seeds.update(seeded_store, SEED_DIR, "kubecon", user_dir=user_dir)
    assert outside.read_bytes() == before


def test_unreadable_seed_event_is_reported_and_refused(seeded_store, tmp_path):
    user_dir = tmp_path / "profiles"
    seed = user_seed(user_dir, "kubecon")
    (seed / EU).write_bytes(b"\xff\xfe not utf-8")
    listing = seeds.status(seeded_store, SEED_DIR, user_dir)
    info = kubecon(listing)
    assert info["state"] == "outdated"
    files = {f["path"]: f for f in info["files"]}
    assert files[EU]["state"] == "unreadable" and str(seed / EU) in files[EU]["error"]
    before = (seeded_store / "profiles" / "kubecon" / "profile.md").read_bytes()
    with pytest.raises(CfpError, match="cannot be read: events/kubecon-eu-2027.md"):
        seeds.update(seeded_store, SEED_DIR, "kubecon", files=[EU], user_dir=user_dir)
    assert (seeded_store / "profiles" / "kubecon" / "profile.md").read_bytes() == before
    result = seeds.update(seeded_store, SEED_DIR, "kubecon", all_files=True, user_dir=user_dir)
    assert result["updated"] == ["profile.md"] and result["skipped"] == [EU]
    # Chosen recovery (see the init skill): the update made the store profile current, so repairing the
    # skipped seed file does not offer it again; raising the seed's seed_version does.
    shutil.copyfile(SEED_DIR / "kubecon" / EU, seed / EU)
    edit(seed / EU, lambda meta: meta.update(tracks=["Repaired Track"]))
    assert kubecon(seeds.status(seeded_store, SEED_DIR, user_dir))["state"] == "current"
    with pytest.raises(CfpError, match="is not outdated"):
        seeds.update(seeded_store, SEED_DIR, "kubecon", files=[EU], user_dir=user_dir)
    edit(seed / "profile.md", lambda meta: meta.update(seed_version="2099-06-01"))
    retry = seeds.update(seeded_store, SEED_DIR, "kubecon", files=[EU], user_dir=user_dir)
    assert EU in retry["updated"] and retry["skipped"] == []


def test_unreadable_seed_file_missing_from_store_is_not_offered(seeded_store, tmp_path):
    user_dir = tmp_path / "profiles"
    seed = user_seed(user_dir, "kubecon")
    (seeded_store / "profiles" / "kubecon" / EU).unlink()
    (seed / EU).write_bytes(b"\xff\xfe not utf-8")
    files = {f["path"]: f for f in kubecon(seeds.status(seeded_store, SEED_DIR, user_dir))["files"]}
    assert files[EU]["state"] == "unreadable"
    before = (seeded_store / "profiles" / "kubecon" / "profile.md").read_bytes()
    with pytest.raises(CfpError, match="cannot be read"):
        seeds.update(seeded_store, SEED_DIR, "kubecon", files=[EU], user_dir=user_dir)
    assert (seeded_store / "profiles" / "kubecon" / "profile.md").read_bytes() == before
    result = seeds.update(seeded_store, SEED_DIR, "kubecon", all_files=True, user_dir=user_dir)
    assert result["skipped"] == [EU] and not (seeded_store / "profiles" / "kubecon" / EU).exists()


def test_update_loads_every_seed_file_before_writing(seeded_store, tmp_path, monkeypatch):
    user_dir = tmp_path / "profiles"
    seed = user_seed(user_dir, "kubecon")
    edit(seed / EU, lambda meta: meta.update(name="changed"))
    real_load = frontmatter.load

    def load(path):
        if path == seed / EU:
            raise CfpError(f"{path}: broke after the status check")
        return real_load(path)

    before = (seeded_store / "profiles" / "kubecon" / "profile.md").read_bytes()
    real_status = seeds._profile_status

    def status_then_break(*args):
        info = real_status(*args)  # the seed file is still fine when the status is taken
        monkeypatch.setattr(seeds.frontmatter, "load", load)
        return info

    monkeypatch.setattr(seeds, "_profile_status", status_then_break)
    with pytest.raises(CfpError, match="broke after the status check"):
        seeds.update(seeded_store, SEED_DIR, "kubecon", all_files=True, user_dir=user_dir)
    assert (seeded_store / "profiles" / "kubecon" / "profile.md").read_bytes() == before


def test_hidden_staging_folder_is_not_a_profile(seeded_store):
    leftover = seeded_store / "profiles" / ".aaa.seeding"
    leftover.mkdir()
    (leftover / "profile.md").write_text("---\nid: aaa\n---\n", encoding="utf-8")
    assert store.list_profile_ids(seeded_store) == ["kubecon"]


def test_collect_skips_user_folder_with_unsafe_name(tmp_path):
    user_dir = tmp_path / "profiles"
    user_seed(user_dir, "acme-summit")
    user_seed(user_dir, "$(touch x)")
    entries, warnings = seeds.collect(SEED_DIR, user_dir)
    assert [e["name"] for e in entries] == ["kubecon", "acme-summit"]
    assert len(warnings) == 1 and warnings[0].startswith(f"profile folder '$(touch x)' in {user_dir} skipped:")


def test_seed_cli_with_user_profiles(seeded_store, run_cli, tmp_path):
    user_dir = tmp_path / "profiles"
    user_seed(user_dir, "kubecon", version=LATER)
    user_seed(user_dir, "acme-summit")
    status = run_cli("profile", "seed-status", "--seed-dir", SEED_DIR, "--user-seed-dir", user_dir)
    assert set(status.data) == {"ok", "seeds", "warnings"}
    assert status["warnings"] == [clash_warning(user_dir)]
    by_name = {seed["profile"]: seed for seed in status["seeds"]}
    assert by_name["kubecon"]["state"] == "outdated" and by_name["kubecon"]["source"] == "user"
    assert by_name["acme-summit"]["state"] == "missing"

    updated = run_cli("profile", "seed-update", "--profile", "kubecon", "--seed-dir", SEED_DIR, "--user-seed-dir", user_dir)
    assert updated["source"] == "user" and updated["warnings"] == [clash_warning(user_dir)]

    unknown = run_cli(
        "profile", "seed-update", "--profile", "nope", "--seed-dir", SEED_DIR, "--user-seed-dir", user_dir, expect_ok=False
    )
    assert unknown.code == 1 and unknown["error"] == f"no seed profile 'nope' in {SEED_DIR} or {user_dir}"


def test_seed_cli_reads_default_user_profiles_dir(seeded_store, run_cli, tmp_home):
    user_dir = tmp_home / ".local" / "share" / "cc-cfp" / "profiles"
    user_seed(user_dir, "acme-summit")
    status = run_cli("profile", "seed-status", "--seed-dir", SEED_DIR)
    assert [seed["profile"] for seed in status["seeds"]] == ["kubecon", "acme-summit"]
    assert status["seeds"][1]["seed_dir"] == str(user_dir / "acme-summit") and status["warnings"] == []
    plain = run_cli("profile", "seed-status", "--seed-dir", SEED_DIR, env={"CFP_DATA_DIR": str(seeded_store.parent / "none")})
    assert [seed["profile"] for seed in plain["seeds"]] == ["kubecon"]


def test_seed_cli_fails_on_relative_data_dir(seeded_store, run_cli):
    for args in (
        ("profile", "seed-status", "--seed-dir", SEED_DIR),
        ("profile", "seed-update", "--profile", "kubecon", "--seed-dir", SEED_DIR),
    ):
        result = run_cli(*args, env={"CFP_DATA_DIR": "rel"}, expect_ok=False)
        assert result.code == 1 and "CFP_DATA_DIR must be an absolute path, got 'rel'" in result["error"]


def test_config_init_cli_seeds_user_profiles_and_merges_warnings(tmp_store, tmp_home, run_cli, tmp_path):
    user_dir = tmp_home / ".local" / "share" / "cc-cfp" / "profiles"
    user_seed(user_dir, "acme-summit")
    user_seed(user_dir, "kubecon", marker="My KubeCon")
    other = tmp_path / "other"
    result = run_cli(
        "config", "init", "--store", tmp_store, "--speaker-name", "A", "--seed-dir", SEED_DIR,
        env={"CFP_STORE": str(other)},
    )
    assert result["seeded_profiles"] == ["kubecon", "acme-summit"]
    assert result["warnings"] == [
        clash_warning(user_dir),
        f"CFP_STORE is set to '{other}' and overrides the saved store '{tmp_store.resolve()}' in later sessions",
    ]
    assert profile.load_profile(tmp_store, "kubecon")["name"] == "My KubeCon"
    assert profile.load_profile(tmp_store, "acme-summit")["approved"] is True

    override = tmp_path / "override"
    user_seed(override, "solo-conf")
    fresh = tmp_path / "fresh"
    result = run_cli(
        "config", "init", "--store", fresh, "--speaker-name", "A", "--seed-dir", SEED_DIR, "--user-seed-dir", override,
        env={"CFP_STORE": None},
    )
    assert result["seeded_profiles"] == ["kubecon", "solo-conf"] and result["warnings"] == []
    assert result["user_profiles_dir"] == str(override)


def test_case_only_variant_of_a_shipped_name_is_skipped(tmp_path):
    """On every file system, so init, status, and update agree (on APFS both names are one store folder)."""
    user_dir = tmp_path / "profiles"
    user_seed(user_dir, "KubeCon")
    entries, warnings = seeds.collect(SEED_DIR, user_dir)
    assert [(e["name"], e["source"]) for e in entries] == [("kubecon", "plugin")]
    assert warnings == [
        f"profile folder 'KubeCon' in {user_dir} skipped: it differs from the shipped profile 'kubecon' only in case; "
        "rename it to 'kubecon' to replace the shipped profile"
    ]


def _case_insensitive(folder):
    probe = folder / "CaseProbe"
    probe.mkdir()
    try:
        return (folder / "caseprobe").exists()
    finally:
        probe.rmdir()


def test_seed_with_a_case_alias_in_the_store_is_never_compared_or_written(seeded_store, tmp_path):
    first = tmp_path / "first"
    user_seed(first, "acme", version="2026-01-01")
    from cfplib import config

    config.init_store(seeded_store, {"speaker_name": "A"}, seed_dir=SEED_DIR, user_seed_dir=first)
    stored = seeded_store / "profiles" / "acme" / "profile.md"
    before = stored.read_bytes()
    second = tmp_path / "second"
    folder = user_seed(second, "ACME")
    listing, warnings = seeds.status_report(seeded_store, SEED_DIR, second)
    if not _case_insensitive(seeded_store / "profiles"):
        assert {s["profile"]: s["state"] for s in listing}["ACME"] == "missing" and warnings == []
        return
    expected = (
        f"profile 'ACME' from {folder} not used: the store already has 'acme', which this file system treats as "
        "the same folder; rename one of them so the names differ in more than case"
    )
    assert [s["profile"] for s in listing] == ["kubecon"] and warnings == [expected]
    with pytest.raises(CfpError) as info:
        seeds.update(seeded_store, SEED_DIR, "ACME", all_files=True, user_dir=second)
    assert str(info.value) == expected
    assert stored.read_bytes() == before
    again = config.init_store(seeded_store, {"speaker_name": "A"}, seed_dir=SEED_DIR, user_seed_dir=second)
    assert again["seeded_profiles"] == [] and again["warnings"] == [expected]


def test_update_refuses_a_symlinked_profiles_folder(tmp_path, tmp_home):
    from cfplib import config

    real = tmp_path / "elsewhere"
    store_dir = tmp_path / "store"
    config.init_store(store_dir, {"speaker_name": "A"}, seed_dir=SEED_DIR)
    shutil.move(str(store_dir / "profiles"), str(real))
    (store_dir / "profiles").symlink_to(real)
    age_store_profile(store_dir)
    before = (real / "kubecon" / "profile.md").read_bytes()
    with pytest.raises(CfpError, match="contains symlinks"):
        seeds.update(store_dir, SEED_DIR, "kubecon", all_files=True)
    assert (real / "kubecon" / "profile.md").read_bytes() == before


def test_check_id_rejects_trailing_newline(tmp_path):
    with pytest.raises(CfpError):
        store.check_id("foo\n", "profile id")
    user_dir = tmp_path / "profiles"
    try:
        user_seed(user_dir, "acme\n")
    except OSError:
        pytest.skip("the file system does not allow a newline in a folder name")
    entries, warnings = seeds.collect(SEED_DIR, user_dir)
    assert [e["name"] for e in entries] == ["kubecon"]
    assert len(warnings) == 1 and "skipped" in warnings[0]


def test_update_error_names_personal_profile(seeded_store, tmp_path):
    user_dir = tmp_path / "profiles"
    user_seed(user_dir, "kubecon")
    with pytest.raises(CfpError) as info:
        seeds.update(seeded_store, SEED_DIR, "kubecon", files=["events/nope.md"], user_dir=user_dir)
    assert "is not a file of the personal profile 'kubecon'; seed files: profile.md" in str(info.value)
    age_store_profile(seeded_store)
    with pytest.raises(CfpError) as info:
        seeds.update(seeded_store, SEED_DIR, "kubecon", files=["events/nope.md"])
    assert "is not a file of the shipped profile 'kubecon'" in str(info.value)


def test_case_alias_on_any_file_system(tmp_path, monkeypatch):
    """Host-independent: drive store.case_alias with a faked lookup, so Linux CI covers the alias branch."""
    import os
    from pathlib import Path

    folder = tmp_path / "profiles"
    folder.mkdir()
    (folder / "acme").mkdir()
    assert store.case_alias(folder, "acme") is None  # exact name
    assert store.case_alias(folder, "zeta") is None  # does not exist
    assert store.case_alias(tmp_path / "missing", "acme") is None  # cannot be listed
    real_exists = Path.exists
    monkeypatch.setattr(Path, "exists", lambda self, *a, **k: self.name == "ACME" or real_exists(self, *a, **k))
    assert store.case_alias(folder, "ACME") == "acme"

    def denied(path):
        raise PermissionError(13, "denied")

    monkeypatch.setattr(os, "listdir", denied)
    assert store.case_alias(folder, "ACME") is None


def test_alias_is_skipped_and_refused_on_any_file_system(seeded_store, tmp_path, monkeypatch):
    user_dir = tmp_path / "profiles"
    folder = user_seed(user_dir, "ACME")
    before = (seeded_store / "profiles" / "kubecon" / "profile.md").read_bytes()
    monkeypatch.setattr(store, "case_alias", lambda directory, name: "acme" if name == "ACME" else None)
    expected = seeds.alias_warning({"name": "ACME", "dir": folder}, "acme")
    listing, warnings = seeds.status_report(seeded_store, SEED_DIR, user_dir)
    assert [s["profile"] for s in listing] == ["kubecon"] and warnings == [expected]
    with pytest.raises(CfpError) as info:
        seeds.update(seeded_store, SEED_DIR, "ACME", all_files=True, user_dir=user_dir)
    assert str(info.value) == expected
    assert (seeded_store / "profiles" / "kubecon" / "profile.md").read_bytes() == before
