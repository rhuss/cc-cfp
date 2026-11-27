"""Tests for store resolution, user config, and store config (cfplib.config)."""

import json
from pathlib import Path

import pytest

from cfplib import CfpError, config
from conftest import SEED_DIR


def test_resolve_store_prefers_cli_then_env_then_user_config(tmp_home, monkeypatch, tmp_path):
    monkeypatch.delenv("CFP_STORE", raising=False)
    default = tmp_home / ".local" / "share" / "cc-cfp" / "store"
    assert config.resolve_store(None) == default
    assert config.resolve_store_with_source(None) == (default, "default")

    config.write_user_config(tmp_path / "from-file")
    assert config.resolve_store(None) == (tmp_path / "from-file").resolve()
    assert config.resolve_store_with_source(None)[1] == "config"

    monkeypatch.setenv("CFP_STORE", str(tmp_path / "from-env"))
    assert config.resolve_store(None) == (tmp_path / "from-env").resolve()
    assert config.resolve_store_with_source(None)[1] == "environment"

    assert config.resolve_store(str(tmp_path / "from-cli")) == (tmp_path / "from-cli").resolve()
    assert config.resolve_store_with_source(str(tmp_path / "from-cli"))[1] == "argument"


def test_user_config_writes_go_to_xdg_and_leave_legacy_untouched(tmp_home, monkeypatch, tmp_path):
    legacy = tmp_home / ".config" / "cc-cfp" / "config.json"
    legacy.parent.mkdir(parents=True)
    legacy.write_text(json.dumps({"store": str(tmp_path / "old"), "keep": "me"}))
    before = legacy.read_bytes()
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))

    assert config.user_config_path() == tmp_path / "cfg" / "cc-cfp" / "config.json"
    assert config.load_user_config()["store"] == str(tmp_path / "old")
    assert config.resolve_store(None) == (tmp_path / "old").resolve()

    written = config.write_user_config(tmp_path / "new")
    assert written == tmp_path / "cfg" / "cc-cfp" / "config.json"
    data = json.loads(written.read_text())
    assert data == {"store": str((tmp_path / "new").resolve()), "keep": "me"}
    assert legacy.read_bytes() == before
    assert config.resolve_store(None) == (tmp_path / "new").resolve()


def test_user_config_follows_cfp_config_dir(tmp_home, monkeypatch, tmp_path):
    monkeypatch.setenv("CFP_CONFIG_DIR", str(tmp_path / "conf"))
    written = config.write_user_config(tmp_path / "s")
    assert written == tmp_path / "conf" / "config.json"
    assert not (tmp_home / ".config").exists()


def test_write_user_config_replaces_malformed_file(tmp_home, tmp_path):
    path = tmp_home / ".config" / "cc-cfp" / "config.json"
    path.parent.mkdir(parents=True)
    path.write_text("not json")
    config.write_user_config(tmp_path / "s")
    assert json.loads(path.read_text()) == {"store": str((tmp_path / "s").resolve())}


def test_user_config_lives_under_home(tmp_home, tmp_path):
    config.write_user_config(tmp_path / "s")
    path = tmp_home / ".config" / "cc-cfp" / "config.json"
    assert path.is_file()
    assert json.loads(path.read_text())["store"] == str((tmp_path / "s").resolve())
    assert config.load_user_config() == {"store": str((tmp_path / "s").resolve())}


def test_load_user_config_tolerates_missing_or_malformed(tmp_home):
    assert config.load_user_config() == {}
    path = tmp_home / ".config" / "cc-cfp" / "config.json"
    path.parent.mkdir(parents=True)
    path.write_text("not json")
    assert config.load_user_config() == {}


def test_init_store_creates_tree_config_and_seeds(tmp_store, tmp_home):
    result = config.init_store(
        tmp_store,
        {"speaker_name": "Test Speaker", "speaker_company": "Example", "review_rounds": 2},
        seed_dir=SEED_DIR,
    )
    for sub in ("profiles", "talks", "proposals", "bios", "resources"):
        assert (tmp_store / sub).is_dir()
    assert (tmp_store / "config.md").is_file()
    assert result["seeded_profiles"] == ["kubecon"]
    assert str(tmp_store / "config.md") in result["created"]

    store_config = config.load_store_config(tmp_store)
    assert store_config["speaker_name"] == "Test Speaker"
    assert store_config["speaker_company"] == "Example"
    assert store_config["review_rounds"] == 2
    assert store_config["voice_profile"] == ""
    assert store_config["default_profile"] == "kubecon"

    assert config.load_user_config()["store"] == str(tmp_store.resolve())

    profile_file = tmp_store / "profiles" / "kubecon" / "profile.md"
    assert profile_file.is_file()
    assert (tmp_store / "profiles" / "kubecon" / "events" / "kubecon-eu-2027.md").is_file()
    assert (tmp_store / "profiles" / "kubecon" / "examples" / "lf-sample-container-runtime.md").is_file()
    from cfplib import frontmatter

    meta, _ = frontmatter.load(profile_file)
    assert meta["approved"] is True
    assert meta["seed_version"] == "2026-10-11"


def test_init_store_does_not_overwrite_existing_profile(tmp_store, tmp_home):
    config.init_store(tmp_store, {"speaker_name": "A"}, seed_dir=SEED_DIR)
    profile_file = tmp_store / "profiles" / "kubecon" / "profile.md"
    profile_file.write_text(profile_file.read_text().replace("approved: true", "approved: false"))
    result = config.init_store(tmp_store, {"speaker_name": "A"}, seed_dir=SEED_DIR)
    assert result["seeded_profiles"] == []
    assert "approved: false" in profile_file.read_text()


def test_init_store_without_seed_dir(tmp_store, tmp_home):
    result = config.init_store(tmp_store, {"speaker_name": "A"}, seed_dir=None)
    assert result["seeded_profiles"] == []
    assert (tmp_store / "profiles").is_dir()


def test_set_store_config_updates_one_key(tmp_store, tmp_home):
    config.init_store(tmp_store, {"speaker_name": "A", "review_rounds": 3}, seed_dir=None)
    config.set_store_config(tmp_store, "review_rounds", "5")
    loaded = config.load_store_config(tmp_store)
    assert loaded["review_rounds"] == 5
    assert loaded["speaker_name"] == "A"
    config.set_store_config(tmp_store, "voice_profile", "blog")
    assert config.load_store_config(tmp_store)["voice_profile"] == "blog"


def test_store_config_keeps_hand_written_body_and_unknown_keys(tmp_store, tmp_home):
    config.init_store(tmp_store, {"speaker_name": "A"}, seed_dir=None)
    path = tmp_store / "config.md"
    path.write_text(path.read_text() + "speaker_gender: woman\n\n## Notes\n\nKept by hand.\n")
    # the appended key lands after the closing delimiter above; rewrite properly
    from cfplib import frontmatter

    meta, body = frontmatter.load(path)
    meta["speaker_gender"] = "woman"
    frontmatter.save(path, meta, "## Notes\n\nKept by hand.\n")
    config.set_store_config(tmp_store, "review_rounds", "4")
    config.init_store(tmp_store, {"speaker_name": "A"}, seed_dir=None)
    meta, body = frontmatter.load(path)
    assert meta["review_rounds"] == 4 and meta["speaker_gender"] == "woman"
    assert "Kept by hand." in body


def test_missing_store_raises_clear_error(tmp_store, tmp_home):
    with pytest.raises(CfpError) as info:
        config.load_store_config(tmp_store)
    assert "config init" in str(info.value)
    assert str(tmp_store) in str(info.value)


def test_require_store_checks_config_file(tmp_store, tmp_home):
    with pytest.raises(CfpError):
        config.require_store(tmp_store)
    config.init_store(tmp_store, {"speaker_name": "A"}, seed_dir=None)
    assert config.require_store(tmp_store) == Path(tmp_store)


def _user_seed(user_dir, name, version):
    import shutil

    from cfplib import frontmatter

    target = user_dir / name
    shutil.copytree(SEED_DIR / "kubecon", target)
    meta, body = frontmatter.load(target / "profile.md")
    meta["id"] = name
    meta["approved"] = False
    if version is None:
        meta.pop("seed_version", None)
    else:
        meta["seed_version"] = version
    frontmatter.save(target / "profile.md", meta, body)
    return target


def test_init_store_seeds_user_profiles(tmp_store, tmp_home, tmp_path):
    from cfplib import frontmatter, seeds

    user_dir = tmp_path / "profiles"
    _user_seed(user_dir, "acme-summit", "2026-01-01")
    _user_seed(user_dir, "kubecon", "2099-01-01")
    _user_seed(user_dir, "no-version", None)
    result = config.init_store(tmp_store, {"speaker_name": "A"}, seed_dir=SEED_DIR, user_seed_dir=user_dir)
    assert result["seeded_profiles"] == ["kubecon", "acme-summit", "no-version"]
    assert result["warnings"] == [
        f"profile 'kubecon': using {user_dir / 'kubecon'} instead of the shipped {SEED_DIR / 'kubecon'}"
    ]
    for name in ("acme-summit", "kubecon", "no-version"):
        assert frontmatter.load(tmp_store / "profiles" / name / "profile.md")[0]["approved"] is True
    assert frontmatter.load(tmp_store / "profiles" / "kubecon" / "profile.md")[0]["seed_version"] == "2099-01-01"
    states = {s["profile"]: s["state"] for s in seeds.status(tmp_store, SEED_DIR, user_dir)}
    assert states == {"kubecon": "current", "acme-summit": "current", "no-version": "local"}


def test_init_store_missing_user_dir_or_none_is_silent(tmp_store, tmp_home, tmp_path):
    result = config.init_store(tmp_store, {"speaker_name": "A"}, seed_dir=SEED_DIR, user_seed_dir=tmp_path / "missing")
    assert result["seeded_profiles"] == ["kubecon"] and result["warnings"] == []
    assert not (tmp_path / "missing").exists()
    result = config.init_store(tmp_store, {"speaker_name": "A"}, seed_dir=SEED_DIR)
    assert result["seeded_profiles"] == [] and result["warnings"] == []


def test_init_store_copies_symlinked_user_profile_as_regular_files(tmp_store, tmp_home, tmp_path):
    from cfplib import frontmatter

    real = _user_seed(tmp_path / "dotfiles", "acme", "2026-01-01")
    source_text = (real / "profile.md").read_text(encoding="utf-8")
    user_dir = tmp_path / "profiles"
    (user_dir / "acme" / "events").mkdir(parents=True)
    (user_dir / "acme" / "profile.md").symlink_to(real / "profile.md")
    (user_dir / "acme" / "examples").symlink_to(real / "examples", target_is_directory=True)
    (user_dir / "acme" / "events" / "linked.md").symlink_to(real / "events" / "kubecon-eu-2027.md")
    (user_dir / "linked-folder").symlink_to(real, target_is_directory=True)

    result = config.init_store(tmp_store, {"speaker_name": "A"}, seed_dir=SEED_DIR, user_seed_dir=user_dir)
    assert result["seeded_profiles"] == ["kubecon", "acme", "linked-folder"]
    copied = tmp_store / "profiles" / "acme"
    assert not (copied / "profile.md").is_symlink() and (copied / "profile.md").is_file()
    assert not (copied / "examples").exists() and not (copied / "events" / "linked.md").exists()
    assert frontmatter.load(copied / "profile.md")[0]["approved"] is True
    folder_copy = tmp_store / "profiles" / "linked-folder"
    assert not folder_copy.is_symlink() and (folder_copy / "events" / "kubecon-eu-2027.md").is_file()
    assert (real / "profile.md").read_text(encoding="utf-8") == source_text


def test_init_store_skips_user_folder_with_unsafe_name(tmp_store, tmp_home, tmp_path):
    user_dir = tmp_path / "profiles"
    _user_seed(user_dir, "bad name;x", "2026-01-01")
    result = config.init_store(tmp_store, {"speaker_name": "A"}, seed_dir=SEED_DIR, user_seed_dir=user_dir)
    assert result["seeded_profiles"] == ["kubecon"]
    assert len(result["warnings"]) == 1 and result["warnings"][0].startswith(
        f"profile folder 'bad name;x' in {user_dir} skipped:"
    )
    assert not (tmp_store / "profiles" / "bad name;x").exists()
    assert config.load_store_config(tmp_store)["default_profile"] == "kubecon"


def test_init_store_skips_broken_user_profile_without_partial_copy(tmp_store, tmp_home, tmp_path):
    from cfplib import seeds

    user_dir = tmp_path / "profiles"
    broken = _user_seed(user_dir, "acme", "2026-01-01")
    good_text = (broken / "profile.md").read_bytes()
    (broken / "profile.md").write_bytes(b"\xff\xfe not utf-8")
    _user_seed(user_dir, "zeta", "2026-01-01")

    result = config.init_store(tmp_store, {"speaker_name": "A"}, seed_dir=SEED_DIR, user_seed_dir=user_dir)
    assert result["seeded_profiles"] == ["kubecon", "zeta"]
    assert len(result["warnings"]) == 1
    assert result["warnings"][0].startswith(f"profile 'acme' from {broken} skipped:")
    assert str(broken / "profile.md") in result["warnings"][0]
    assert not (tmp_store / "profiles" / "acme").exists()
    assert not list((tmp_store / "profiles").glob(".*"))
    assert config.load_user_config()["store"] == str(tmp_store.resolve())

    listing = {s["profile"]: s for s in seeds.status(tmp_store, SEED_DIR, user_dir)}
    assert listing["acme"]["state"] == "unreadable" and str(broken / "profile.md") in listing["acme"]["error"]
    assert listing["kubecon"]["state"] == "current" and listing["zeta"]["state"] == "current"

    (broken / "profile.md").write_bytes(good_text)
    again = config.init_store(tmp_store, {"speaker_name": "A"}, seed_dir=SEED_DIR, user_seed_dir=user_dir)
    assert again["seeded_profiles"] == ["acme"] and again["warnings"] == []


def test_broken_shipped_seed_still_fails_without_partial_copy(tmp_store, tmp_home, tmp_path):
    plugin_dir = tmp_path / "plugin"
    shipped = _user_seed(plugin_dir, "kubecon", "2026-01-01")
    (shipped / "profile.md").write_bytes(b"\xff\xfe not utf-8")
    with pytest.raises(CfpError):
        config.init_store(tmp_store, {"speaker_name": "A"}, seed_dir=plugin_dir)
    assert not list((tmp_store / "profiles").iterdir())
