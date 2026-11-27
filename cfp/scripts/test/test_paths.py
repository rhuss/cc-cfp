"""Tests for the shared path resolver (cfplib.paths), per contracts/paths.md.

Every call passes ``env`` and ``home`` explicitly, so the real environment
never leaks in.
"""

import json
import os
from pathlib import Path

import pytest

from cfplib import CfpError, paths


@pytest.fixture
def home(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    return home


def write_config(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")
    return path


# ---------------------------------------------------------------- config folder


def test_config_dir_default_is_home_config(home):
    assert paths.config_dir(env={}, home=home) == home / ".config" / "cc-cfp"
    assert paths.config_file(env={}, home=home) == home / ".config" / "cc-cfp" / "config.json"


def test_config_dir_uses_xdg_config_home(home, tmp_path):
    env = {"XDG_CONFIG_HOME": str(tmp_path / "cfg")}
    assert paths.config_dir(env=env, home=home) == tmp_path / "cfg" / "cc-cfp"


def test_cfp_config_dir_wins_over_xdg(home, tmp_path):
    env = {"XDG_CONFIG_HOME": str(tmp_path / "cfg"), "CFP_CONFIG_DIR": str(tmp_path / "mine")}
    assert paths.config_dir(env=env, home=home) == tmp_path / "mine"
    assert paths.config_file(env=env, home=home) == tmp_path / "mine" / "config.json"


@pytest.mark.parametrize("value", ["", "relative/cfg", "cfg"])
def test_xdg_config_home_ignored_when_empty_or_relative(home, value):
    assert paths.config_dir(env={"XDG_CONFIG_HOME": value}, home=home) == home / ".config" / "cc-cfp"


@pytest.mark.parametrize("value", ["", "   ", "\t"])
def test_blank_cfp_config_dir_counts_as_unset(home, value):
    assert paths.config_dir(env={"CFP_CONFIG_DIR": value}, home=home) == home / ".config" / "cc-cfp"


def test_cfp_config_dir_expands_tilde(home):
    assert paths.config_dir(env={"CFP_CONFIG_DIR": "~/conf"}, home=home) == home / "conf"


def test_relative_cfp_config_dir_is_rejected(home):
    with pytest.raises(CfpError) as info:
        paths.config_dir(env={"CFP_CONFIG_DIR": "conf"}, home=home)
    assert str(info.value) == "CFP_CONFIG_DIR must be an absolute path, got 'conf'"


def test_legacy_config_file(home):
    assert paths.legacy_config_file(home=home) == home / ".config" / "cc-cfp" / "config.json"


# ---------------------------------------------------------------- data folder


def test_data_dir_default(home):
    assert paths.data_dir(env={}, home=home) == home / ".local" / "share" / "cc-cfp"
    assert paths.user_profiles_dir(env={}, home=home) == home / ".local" / "share" / "cc-cfp" / "profiles"
    assert paths.default_store(env={}, home=home) == home / ".local" / "share" / "cc-cfp" / "store"


def test_data_dir_uses_xdg_data_home(home, tmp_path):
    env = {"XDG_DATA_HOME": str(tmp_path / "data")}
    assert paths.data_dir(env=env, home=home) == tmp_path / "data" / "cc-cfp"
    assert paths.default_store(env=env, home=home) == tmp_path / "data" / "cc-cfp" / "store"


def test_cfp_data_dir_wins_over_xdg(home, tmp_path):
    env = {"XDG_DATA_HOME": str(tmp_path / "data"), "CFP_DATA_DIR": str(tmp_path / "team")}
    assert paths.data_dir(env=env, home=home) == tmp_path / "team"
    assert paths.user_profiles_dir(env=env, home=home) == tmp_path / "team" / "profiles"
    assert paths.default_store(env=env, home=home) == tmp_path / "team" / "store"


@pytest.mark.parametrize("value", ["", "data", "rel/data"])
def test_xdg_data_home_ignored_when_empty_or_relative(home, value):
    assert paths.data_dir(env={"XDG_DATA_HOME": value}, home=home) == home / ".local" / "share" / "cc-cfp"


@pytest.mark.parametrize("value", ["", "  "])
def test_blank_cfp_data_dir_counts_as_unset(home, value):
    assert paths.data_dir(env={"CFP_DATA_DIR": value}, home=home) == home / ".local" / "share" / "cc-cfp"


def test_cfp_data_dir_expands_tilde(home):
    assert paths.data_dir(env={"CFP_DATA_DIR": "~/d"}, home=home) == home / "d"


def test_relative_cfp_data_dir_is_rejected(home):
    for func in (paths.data_dir, paths.user_profiles_dir, paths.default_store):
        with pytest.raises(CfpError) as info:
            func(env={"CFP_DATA_DIR": "rel"}, home=home)
        assert str(info.value) == "CFP_DATA_DIR must be an absolute path, got 'rel'"


def test_nothing_is_created(home, tmp_path):
    env = {"CFP_DATA_DIR": str(tmp_path / "d"), "CFP_CONFIG_DIR": str(tmp_path / "c")}
    paths.config_file(env=env, home=home)
    paths.read_config(env=env, home=home)
    paths.user_profiles_dir(env=env, home=home)
    paths.resolve_store(None, env=env, home=home)
    assert not (tmp_path / "d").exists() and not (tmp_path / "c").exists()
    assert list(home.iterdir()) == []


# ---------------------------------------------------------------- read_config


def test_read_config_missing_everywhere(home):
    assert paths.read_config(env={}, home=home) == ({}, None)


def test_read_config_reads_resolved_file(home, tmp_path):
    path = write_config(tmp_path / "cfg" / "cc-cfp" / "config.json", {"store": "/s", "extra": 1})
    data, read = paths.read_config(env={"XDG_CONFIG_HOME": str(tmp_path / "cfg")}, home=home)
    assert data == {"store": "/s", "extra": 1} and read == path


def test_read_config_legacy_fallback_when_resolved_missing(home, tmp_path):
    legacy = write_config(home / ".config" / "cc-cfp" / "config.json", {"store": "/old"})
    data, read = paths.read_config(env={"XDG_CONFIG_HOME": str(tmp_path / "cfg")}, home=home)
    assert data == {"store": "/old"} and read == legacy


def test_read_config_no_legacy_fallback_with_cfp_config_dir(home, tmp_path):
    write_config(home / ".config" / "cc-cfp" / "config.json", {"store": "/old"})
    assert paths.read_config(env={"CFP_CONFIG_DIR": str(tmp_path / "c")}, home=home) == ({}, None)


def test_read_config_empty_cfp_config_dir_keeps_legacy_fallback(home, tmp_path):
    legacy = write_config(home / ".config" / "cc-cfp" / "config.json", {"store": "/old"})
    env = {"CFP_CONFIG_DIR": " ", "XDG_CONFIG_HOME": str(tmp_path / "cfg")}
    assert paths.read_config(env=env, home=home) == ({"store": "/old"}, legacy)


@pytest.mark.parametrize("content", ["not json", "[1, 2]", "\"text\"", ""])
def test_read_config_malformed_resolved_file_has_no_fallback(home, tmp_path, content):
    write_config(home / ".config" / "cc-cfp" / "config.json", {"store": "/old"})
    path = write_config(tmp_path / "cfg" / "cc-cfp" / "config.json", content)
    assert paths.read_config(env={"XDG_CONFIG_HOME": str(tmp_path / "cfg")}, home=home) == ({}, path)


def test_read_config_resolved_file_without_store_has_no_fallback(home, tmp_path):
    write_config(home / ".config" / "cc-cfp" / "config.json", {"store": "/old"})
    path = write_config(tmp_path / "cfg" / "cc-cfp" / "config.json", {"other": True})
    env = {"XDG_CONFIG_HOME": str(tmp_path / "cfg")}
    assert paths.read_config(env=env, home=home) == ({"other": True}, path)
    store, source = paths.resolve_store(None, env=env, home=home)
    assert source == "default" and store == home / ".local" / "share" / "cc-cfp" / "store"


def test_read_config_relative_cfp_config_dir_raises(home):
    with pytest.raises(CfpError, match="CFP_CONFIG_DIR must be an absolute path"):
        paths.read_config(env={"CFP_CONFIG_DIR": "rel"}, home=home)


# ---------------------------------------------------------------- resolve_store


def test_resolve_store_default(home):
    assert paths.resolve_store(None, env={}, home=home) == (home / ".local" / "share" / "cc-cfp" / "store", "default")


def test_resolve_store_default_follows_xdg_data_home(home, tmp_path):
    env = {"XDG_DATA_HOME": str(tmp_path / "data")}
    assert paths.resolve_store(None, env=env, home=home) == (tmp_path / "data" / "cc-cfp" / "store", "default")


def test_resolve_store_from_config(home, tmp_path):
    write_config(home / ".config" / "cc-cfp" / "config.json", {"store": str(tmp_path / "s")})
    assert paths.resolve_store(None, env={}, home=home) == (tmp_path / "s", "config")


def test_resolve_store_config_value_tilde_expanded(home):
    write_config(home / ".config" / "cc-cfp" / "config.json", {"store": "~/talks"})
    assert paths.resolve_store(None, env={}, home=home) == (home / "talks", "config")


def test_resolve_store_config_value_relative_to_config_folder(home, tmp_path):
    write_config(tmp_path / "c" / "config.json", {"store": "talks"})
    env = {"CFP_CONFIG_DIR": str(tmp_path / "c")}
    assert paths.resolve_store(None, env=env, home=home) == (tmp_path / "c" / "talks", "config")


def test_resolve_store_legacy_config_relative_to_legacy_folder(home, tmp_path):
    write_config(home / ".config" / "cc-cfp" / "config.json", {"store": "talks"})
    env = {"XDG_CONFIG_HOME": str(tmp_path / "cfg")}
    assert paths.resolve_store(None, env=env, home=home) == (home / ".config" / "cc-cfp" / "talks", "config")


@pytest.mark.parametrize("value", [None, 42, ["/x"], {"a": 1}, "", "  "])
def test_resolve_store_ignores_non_string_or_empty_config_value(home, value):
    write_config(home / ".config" / "cc-cfp" / "config.json", {"store": value})
    assert paths.resolve_store(None, env={}, home=home)[1] == "default"


def test_resolve_store_environment(home, tmp_path):
    write_config(home / ".config" / "cc-cfp" / "config.json", {"store": str(tmp_path / "file")})
    env = {"CFP_STORE": str(tmp_path / "env")}
    assert paths.resolve_store(None, env=env, home=home) == (tmp_path / "env", "environment")


def test_resolve_store_environment_tilde_expanded(home):
    assert paths.resolve_store(None, env={"CFP_STORE": "~/x"}, home=home) == (home / "x", "environment")


@pytest.mark.parametrize("value", ["", "   "])
def test_blank_cfp_store_counts_as_unset(home, value):
    assert paths.resolve_store(None, env={"CFP_STORE": value}, home=home)[1] == "default"


def test_relative_cfp_store_is_rejected(home):
    with pytest.raises(CfpError) as info:
        paths.resolve_store(None, env={"CFP_STORE": "talks"}, home=home)
    assert str(info.value) == "CFP_STORE must be an absolute path, got 'talks'"


def test_resolve_store_argument_wins(home, tmp_path):
    write_config(home / ".config" / "cc-cfp" / "config.json", {"store": str(tmp_path / "file")})
    env = {"CFP_STORE": str(tmp_path / "env")}
    assert paths.resolve_store(str(tmp_path / "cli"), env=env, home=home) == (tmp_path / "cli", "argument")


def test_resolve_store_relative_argument_resolved_against_cwd(home, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    store, source = paths.resolve_store("mystore", env={}, home=home)
    assert source == "argument" and store == (tmp_path / "mystore").resolve()


def test_resolve_store_argument_tilde_expanded(home):
    assert paths.resolve_store("~/s", env={}, home=home) == (home / "s", "argument")


def test_resolved_store_is_absolute_and_normalized(home, tmp_path):
    store, _ = paths.resolve_store(None, env={"CFP_STORE": str(tmp_path / "a" / ".." / "b")}, home=home)
    assert store == (tmp_path / "b").resolve() and store.is_absolute()


# ---------------------------------------------------------------- lazy evaluation


BROKEN_ALL = {"CFP_STORE": "rel-store", "CFP_CONFIG_DIR": "rel-config", "CFP_DATA_DIR": "rel-data"}


def test_argument_ignores_broken_later_variables(home, tmp_path):
    assert paths.resolve_store(str(tmp_path / "cli"), env=BROKEN_ALL, home=home) == (tmp_path / "cli", "argument")


def test_valid_cfp_store_ignores_broken_config_and_data_dir(home, tmp_path):
    env = {"CFP_STORE": str(tmp_path / "env"), "CFP_CONFIG_DIR": "rel-config", "CFP_DATA_DIR": "rel-data"}
    assert paths.resolve_store(None, env=env, home=home) == (tmp_path / "env", "environment")


def test_config_store_ignores_broken_data_dir(home, tmp_path):
    write_config(home / ".config" / "cc-cfp" / "config.json", {"store": str(tmp_path / "file")})
    env = {"CFP_DATA_DIR": "rel-data"}
    assert paths.resolve_store(None, env=env, home=home) == (tmp_path / "file", "config")


def test_broken_config_dir_reached_raises(home):
    with pytest.raises(CfpError, match="CFP_CONFIG_DIR must be an absolute path, got 'rel-config'"):
        paths.resolve_store(None, env={"CFP_CONFIG_DIR": "rel-config"}, home=home)


def test_broken_data_dir_reached_as_fallback_raises(home):
    with pytest.raises(CfpError, match="CFP_DATA_DIR must be an absolute path, got 'rel-data'"):
        paths.resolve_store(None, env={"CFP_DATA_DIR": "rel-data"}, home=home)


def test_defaults_use_os_environ_and_home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    for name in ("XDG_CONFIG_HOME", "XDG_DATA_HOME", "CFP_CONFIG_DIR", "CFP_DATA_DIR", "CFP_STORE"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("CFP_DATA_DIR", str(tmp_path / "d"))
    assert paths.data_dir() == tmp_path / "d"
    assert paths.config_dir() == Path(os.environ["HOME"]) / ".config" / "cc-cfp"
    assert paths.resolve_store(None) == ((tmp_path / "d" / "store").resolve(), "default")
