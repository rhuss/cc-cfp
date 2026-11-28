"""Where cfp keeps its config, its data, and the store.

This is the single resolver shared by ``cfp_store.py`` (through
``cfplib.config``) and the session context hook, so both always agree on the
active store. It imports nothing from cfplib except ``CfpError`` and never
creates folders.

Config folder: ``CFP_CONFIG_DIR``, else ``$XDG_CONFIG_HOME/cc-cfp``, else
``~/.config/cc-cfp``; the file inside is ``config.json``. When
``CFP_CONFIG_DIR`` is unset and that file does not exist, the feature 001
location ``~/.config/cc-cfp/config.json`` is read as a legacy fallback.

Data folder: ``CFP_DATA_DIR``, else ``$XDG_DATA_HOME/cc-cfp``, else
``~/.local/share/cc-cfp``. It holds ``profiles/`` (personal seed profiles)
and the default ``store/``.

Store: ``--store``, then ``CFP_STORE``, then the ``store`` entry of the
config file, then ``<data folder>/store``. Resolution is lazy: it stops at
the first step that yields a store, so a broken variable of a later step is
never read.

Every function takes ``env`` (default ``os.environ``) and ``home`` (default
``Path.home()``) so tests can drive them without touching the real system.
"""

import json
import os
import stat
from pathlib import Path

from cfplib import CfpError

APP = "cc-cfp"
CONFIG_NAME = "config.json"


def _env(env):
    return os.environ if env is None else env


def _home(home):
    return Path.home() if home is None else Path(home)


def _expand(value, home):
    """Expand a leading ``~`` against ``home`` (``~user`` goes through the OS)."""
    if value == "~":
        return str(home)
    if value.startswith("~/"):
        return str(home / value[2:])
    if value.startswith("~"):
        return os.path.expanduser(value)
    return value


def _cfp_var(name, env, home):
    """A CFP_* path variable as an absolute Path, or None when unset or blank."""
    raw = _env(env).get(name, "")
    raw = raw.strip() if isinstance(raw, str) else ""
    if not raw:
        return None
    expanded = _expand(raw, _home(home))
    if not os.path.isabs(expanded):
        raise CfpError(f"{name} must be an absolute path, got '{raw}'")
    return Path(expanded)


def _xdg_var(name, env):
    """An XDG base folder, or None when empty or not absolute (the XDG spec says to ignore it)."""
    value = _env(env).get(name, "")
    if isinstance(value, str) and value and os.path.isabs(value):
        return Path(value)
    return None


def config_dir(env=None, home=None):
    explicit = _cfp_var("CFP_CONFIG_DIR", env, home)
    if explicit is not None:
        return explicit
    xdg = _xdg_var("XDG_CONFIG_HOME", env)
    if xdg is not None:
        return xdg / APP
    return _home(home) / ".config" / APP


def config_file(env=None, home=None):
    return config_dir(env, home) / CONFIG_NAME


def legacy_config_file(home=None):
    return _home(home) / ".config" / APP / CONFIG_NAME


def _load_json_object(path):
    """The JSON object in ``path``; {} when it is malformed or holds no object.

    A file that exists but cannot be read raises CfpError: silently treating it
    as empty would send every command to the default store.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    except UnicodeDecodeError:
        return {}
    except OSError as error:
        raise CfpError(f"cannot read the config file {path}: {error.strerror or error}") from None
    try:
        data = json.loads(text)
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def read_config(env=None, home=None):
    """Return ``(data, read_path)`` for the config file in effect.

    ``read_path`` is None when no file was found. A file that exists but is
    malformed or holds no JSON object gives ``({}, path)``; it never leads to
    the legacy fallback. A file that exists but cannot be read raises CfpError.
    """
    path = config_file(env, home)
    if path.exists():
        return _load_json_object(path), path
    if _cfp_var("CFP_CONFIG_DIR", env, home) is None:
        legacy = legacy_config_file(home)
        if legacy != path and legacy.exists():
            return _load_json_object(legacy), legacy
    return {}, None


def data_dir(env=None, home=None):
    explicit = _cfp_var("CFP_DATA_DIR", env, home)
    if explicit is not None:
        return explicit
    xdg = _xdg_var("XDG_DATA_HOME", env)
    if xdg is not None:
        return xdg / APP
    return _home(home) / ".local" / "share" / APP


def user_profiles_dir(env=None, home=None):
    return data_dir(env, home) / "profiles"


def default_store(env=None, home=None):
    return data_dir(env, home) / "store"


def env_store(env=None, home=None):
    """``CFP_STORE`` as an absolute Path, or None when unset or blank."""
    return _cfp_var("CFP_STORE", env, home)


def resolve_store(cli_store, env=None, home=None):
    """Return ``(store, source)`` with source ``argument|environment|config|default``.

    A relative ``cli_store`` is resolved against the current folder, since the
    user typed it there. The returned path is absolute and normalized.
    """
    if cli_store:
        return Path(_expand(str(cli_store), _home(home))).resolve(), "argument"
    from_env = env_store(env, home)
    if from_env is not None:
        return from_env.resolve(), "environment"
    data, read_path = read_config(env, home)
    value = data.get("store")
    if isinstance(value, str) and value.strip():
        candidate = Path(_expand(value.strip(), _home(home)))
        if not candidate.is_absolute():
            candidate = read_path.parent / candidate
        return candidate.resolve(), "config"
    return default_store(env, home).resolve(), "default"


def store_initialized(store):
    """True when ``<store>/config.md`` is a regular file, False when it does not exist.

    Uses ``os.stat``, not ``Path.is_file``: since Python 3.14 ``is_file()``
    hides a PermissionError as False, which would make a store the process
    cannot read look uninitialized. Any other access error raises CfpError.
    The CLI and the session hook share this check.
    """
    config_md = Path(store) / "config.md"
    try:
        return stat.S_ISREG(os.stat(config_md).st_mode)
    except (FileNotFoundError, NotADirectoryError):
        return False
    except OSError as error:
        raise CfpError(f"cannot access {config_md}: {error.strerror or error}") from None
