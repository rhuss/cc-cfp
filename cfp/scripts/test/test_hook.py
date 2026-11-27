"""The session context hook and the CLI resolve the same store (FR-004, SC-003)."""

import itertools
import json
import os
import re
import subprocess
import sys
from xml.sax.saxutils import unescape

import pytest

from conftest import CLI, PATH_ENV_VARS, PLUGIN_DIR

HOOK = PLUGIN_DIR / "hooks" / "scripts" / "context-hook.py"


def clean_env(home, **extra):
    env = {k: v for k, v in os.environ.items() if k not in PATH_ENV_VARS}
    env["HOME"] = str(home)
    env.update({k: str(v) for k, v in extra.items()})
    return env


def run_hook(env, prompt="/cfp:status"):
    completed = subprocess.run(
        [sys.executable, "-I", str(HOOK)],
        input=json.dumps({"prompt": prompt}),
        capture_output=True,
        text=True,
        env=env,
    )
    assert completed.returncode == 0, completed.stderr
    return completed.stdout


def context_of(stdout):
    data = json.loads(stdout)
    return data["hookSpecificOutput"]["additionalContext"]


def element(context, name):
    match = re.search(rf"<{name}>(.*?)</{name}>", context, re.S)
    return None if match is None else match.group(1)


def run_cli(env, *args):
    completed = subprocess.run(
        [sys.executable, "-I", str(CLI)] + [str(a) for a in args], capture_output=True, text=True, env=env
    )
    return completed.returncode, json.loads(completed.stdout)


LOCATIONS = ("cfp_config_dir", "xdg_config_home", "home", "legacy")
MATRIX = list(itertools.product((False, True), LOCATIONS, (False, True), (False, True)))


def build_case(tmp_path, home, cfp_store, location, entry, data_dir):
    """Set up one SC-003 combination; return (env vars, expected store)."""
    extra = {}
    config_store = tmp_path / "from-config"
    if location == "cfp_config_dir":
        extra["CFP_CONFIG_DIR"] = tmp_path / "cdir"
        config_file = tmp_path / "cdir" / "config.json"
    elif location == "xdg_config_home":
        extra["XDG_CONFIG_HOME"] = tmp_path / "xdg"
        config_file = tmp_path / "xdg" / "cc-cfp" / "config.json"
    elif location == "home":
        config_file = home / ".config" / "cc-cfp" / "config.json"
    else:  # legacy: XDG points to a folder without a cfp config
        extra["XDG_CONFIG_HOME"] = tmp_path / "xdg-empty"
        config_file = home / ".config" / "cc-cfp" / "config.json"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text(json.dumps({"store": str(config_store)} if entry else {"unrelated": 1}))
    if cfp_store:
        extra["CFP_STORE"] = tmp_path / "from-env"
    if data_dir:
        extra["CFP_DATA_DIR"] = tmp_path / "data"

    if cfp_store:
        expected = tmp_path / "from-env"
    elif entry:
        expected = config_store
    elif data_dir:
        expected = tmp_path / "data" / "store"
    else:
        expected = home / ".local" / "share" / "cc-cfp" / "store"
    return clean_env(home, **extra), expected.resolve()


@pytest.mark.parametrize("cfp_store,location,entry,data_dir", MATRIX)
def test_hook_and_cli_agree(tmp_path, cfp_store, location, entry, data_dir):
    home = tmp_path / "home"
    home.mkdir()
    env, expected = build_case(tmp_path, home, cfp_store, location, entry, data_dir)

    context = context_of(run_hook(env))
    code, shown = run_cli(env, "config", "show")
    assert code == 0, shown
    assert unescape(element(context, "store")) == shown["store"] == str(expected)
    assert element(context, "store-error") is None
    assert element(context, "store-initialized") == "false"

    explicit = tmp_path / "explicit"
    code, shown = run_cli(env, "config", "show", "--store", explicit)
    assert code == 0 and shown["store"] == str(explicit.resolve()) and shown["store_source"] == "argument"


@pytest.mark.parametrize("cfp_store,location,entry", list(itertools.product((False, True), LOCATIONS, (False, True))))
def test_explicit_store_wins_even_with_broken_data_dir(tmp_path, cfp_store, location, entry):
    home = tmp_path / "home"
    home.mkdir()
    env, _ = build_case(tmp_path, home, cfp_store, location, entry, False)
    env["CFP_DATA_DIR"] = "rel"
    code, shown = run_cli(env, "config", "show")
    assert code == 1 and "CFP_DATA_DIR must be an absolute path" in shown["error"]
    explicit = tmp_path / "explicit"
    code, listed = run_cli(env, "profile", "list", "--store", explicit)
    assert code == 1 and "store not initialized at " + str(explicit.resolve()) in listed["error"]


def test_hook_reports_initialized_store(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    store = tmp_path / "store"
    env = clean_env(home)
    code, result = run_cli(env, "config", "init", "--store", store, "--speaker-name", "A")
    assert code == 0, result
    context = context_of(run_hook(env))
    assert element(context, "store") == str(store.resolve())
    assert element(context, "store-initialized") == "true"


def test_relative_cfp_store_yields_store_error(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    context = context_of(run_hook(clean_env(home, CFP_STORE="talks")))
    assert element(context, "store") == ""
    assert element(context, "store-initialized") == "false"
    assert element(context, "store-error") == "CFP_STORE must be an absolute path, got 'talks'"
    assert element(context, "plugin-root") == str(PLUGIN_DIR)
    assert element(context, "today")


@pytest.mark.parametrize("name", ["CFP_CONFIG_DIR", "CFP_DATA_DIR"])
def test_other_relative_variables_yield_store_error(tmp_path, name):
    home = tmp_path / "home"
    home.mkdir()
    context = context_of(run_hook(clean_env(home, **{name: "rel"})))
    assert element(context, "store") == ""
    assert element(context, "store-error") == f"{name} must be an absolute path, got 'rel'"


def test_store_path_is_xml_escaped(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    store = tmp_path / "a&b<c>"
    context = context_of(run_hook(clean_env(home, CFP_STORE=store)))
    raw = element(context, "store")
    assert "&amp;" in raw and "&lt;" in raw and "&gt;" in raw
    assert unescape(raw) == str(store.resolve())


@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0, reason="root ignores folder permissions")
def test_unreadable_store_yields_store_error(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    locked = tmp_path / "locked"
    store = locked / "store"
    store.mkdir(parents=True)
    (store / "config.md").write_text("---\n---\n", encoding="utf-8")
    locked.chmod(0)
    try:
        context = context_of(run_hook(clean_env(home, CFP_STORE=store)))
    finally:
        locked.chmod(0o755)
    assert element(context, "store") == ""
    assert element(context, "store-initialized") == "false"
    error = element(context, "store-error")
    assert error.startswith(f"cannot access {store / 'config.md'}:") and "ermission" in error


def test_store_check_does_not_rely_on_path_is_file(tmp_path, monkeypatch, capsys):
    """Since Python 3.14 Path.is_file() returns False on a PermissionError; the hook must not depend on it."""
    import importlib.util
    import io
    from pathlib import Path

    spec = importlib.util.spec_from_file_location("cfp_context_hook", HOOK)
    hook = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hook)
    for name in PATH_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("CFP_STORE", str(tmp_path / "store"))
    monkeypatch.setattr(Path, "is_file", lambda self: False)
    def denied(path):
        raise PermissionError(13, "Permission denied")

    # The hook checks through cfplib.paths; replace only that module's reference to os, not os.stat
    # for the whole process.
    from cfplib import paths

    monkeypatch.setattr(paths, "os", type("FakeOs", (), {"stat": staticmethod(denied), "__getattr__": lambda self, name: getattr(os, name)})())
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"prompt": "/cfp:status"})))
    assert hook.main() == 0
    context = context_of(capsys.readouterr().out)
    assert element(context, "store") == ""
    assert element(context, "store-error") == f"cannot access {tmp_path / 'store' / 'config.md'}: Permission denied"


def test_store_error_is_xml_escaped(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    context = context_of(run_hook(clean_env(home, CFP_STORE="a&b")))
    assert element(context, "store-error") == "CFP_STORE must be an absolute path, got 'a&amp;b'"


def test_non_cfp_prompt_yields_no_output(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    assert run_hook(clean_env(home), prompt="hello") == ""
