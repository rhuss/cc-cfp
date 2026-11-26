"""Tests for store resolution, user config, and store config (cfplib.config)."""

import json
from pathlib import Path

import pytest

from cfplib import CfpError, config
from conftest import SEED_DIR


def test_resolve_store_prefers_cli_then_env_then_user_config(tmp_home, monkeypatch, tmp_path):
    monkeypatch.delenv("CFP_STORE", raising=False)
    with pytest.raises(CfpError):
        config.resolve_store(None)

    config.write_user_config(tmp_path / "from-file")
    assert config.resolve_store(None) == (tmp_path / "from-file").resolve()

    monkeypatch.setenv("CFP_STORE", str(tmp_path / "from-env"))
    assert config.resolve_store(None) == (tmp_path / "from-env").resolve()

    assert config.resolve_store(str(tmp_path / "from-cli")) == (tmp_path / "from-cli").resolve()


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
