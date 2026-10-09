"""Shared pytest fixtures for the cfp_store.py library and CLI tests."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

TEST_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TEST_DIR.parent
PLUGIN_DIR = SCRIPTS_DIR.parent
SEED_DIR = PLUGIN_DIR / "knowledge-base" / "profiles"
TEMPLATES_DIR = PLUGIN_DIR / "knowledge-base" / "templates"
CLI = SCRIPTS_DIR / "cfp_store.py"
TODAY = "2026-10-09"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


@pytest.fixture
def tmp_home(tmp_path, monkeypatch):
    """Isolated HOME so tests never touch the real ~/.config/cc-cfp."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    return home


@pytest.fixture
def tmp_store(tmp_path, tmp_home, monkeypatch):
    """Path to an uninitialized store; env CFP_STORE points at it."""
    store = tmp_path / "store"
    monkeypatch.setenv("CFP_STORE", str(store))
    return store


@pytest.fixture
def seeded_store(tmp_store):
    """Store initialized through the config init code path with the seed profiles."""
    from cfplib import config

    config.init_store(
        tmp_store,
        {
            "speaker_name": "Test Speaker",
            "speaker_company": "Example Corp",
            "voice_profile": "",
            "review_rounds": 3,
            "default_profile": "kubecon",
        },
        seed_dir=SEED_DIR,
    )
    return tmp_store


class CliResult:
    def __init__(self, completed):
        self.code = completed.returncode
        self.stdout = completed.stdout
        self.stderr = completed.stderr
        try:
            self.data = json.loads(completed.stdout) if completed.stdout.strip() else None
        except json.JSONDecodeError:
            self.data = None

    def __getitem__(self, key):
        return self.data[key]

    def get(self, key, default=None):
        return self.data.get(key, default) if isinstance(self.data, dict) else default


@pytest.fixture
def run_cli(tmp_store):
    """Invoke cfp_store.py in a subprocess with python3 -I and parse JSON stdout."""

    def _run(*args, expect_ok=True, today=TODAY, env=None):
        cmd = [sys.executable, "-I", str(CLI)]
        if today:
            cmd += ["--today", today]
        cmd += [str(a) for a in args]
        run_env = dict(os.environ)
        if env:
            run_env.update(env)
        completed = subprocess.run(cmd, capture_output=True, text=True, env=run_env)
        result = CliResult(completed)
        if expect_ok:
            assert result.code == 0, f"exit {result.code}: stdout={completed.stdout!r} stderr={completed.stderr!r}"
            assert result.data is not None and result.data.get("ok") is True, completed.stdout
        return result

    return _run


@pytest.fixture
def write_json(tmp_path):
    """Write a dict to a JSON file inside tmp_path and return its path."""
    counter = {"n": 0}

    def _write(data, name=None):
        counter["n"] += 1
        path = tmp_path / (name or f"input-{counter['n']}.json")
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    return _write


@pytest.fixture
def write_text(tmp_path):
    """Write text to a file inside tmp_path and return its path."""
    counter = {"n": 0}

    def _write(text, name=None):
        counter["n"] += 1
        path = tmp_path / (name or f"text-{counter['n']}.txt")
        path.write_text(text, encoding="utf-8")
        return path

    return _write
