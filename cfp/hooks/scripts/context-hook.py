#!/usr/bin/env python3
"""UserPromptSubmit hook for the cfp plugin.

Reads the hook input JSON from stdin and, when the prompt starts with
``/cfp:``, emits an ``additionalContext`` block that tells the skills where
the plugin lives, where the store is, and whether the store is initialized.

The store is resolved by ``cfplib.paths``, the same module the CLI uses, so
the hook and ``cfp_store.py`` never disagree (``CFP_STORE``, the config file
in ``CFP_CONFIG_DIR``, ``$XDG_CONFIG_HOME/cc-cfp`` or ``~/.config/cc-cfp``,
then ``<data folder>/store``). The hook runs as ``python3 -I``, which ignores
``PYTHONPATH``, so it puts ``<plugin root>/scripts`` on ``sys.path`` itself.

The hook never exits non-zero for a ``/cfp:`` prompt. When resolution fails
(for example a relative ``CFP_STORE``), ``<store>`` is empty, the store is
reported as not initialized, and ``<store-error>`` carries the message.
"""

import datetime
import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape

# hooks/scripts/context-hook.py -> hooks/scripts -> hooks -> plugin root
PLUGIN_ROOT = Path(__file__).resolve().parent.parent.parent


def read_hook_input():
    try:
        return json.loads(sys.stdin.read() or "{}")
    except (json.JSONDecodeError, ValueError):
        return {}


def resolve_store():
    """Return ``(store path or "", error message or None)``."""
    try:
        scripts = str(PLUGIN_ROOT / "scripts")
        if scripts not in sys.path:
            sys.path.insert(0, scripts)
        from cfplib import paths

        store, _source = paths.resolve_store(None)
        return str(store), None
    except Exception as error:  # noqa: BLE001  the hook must never fail a /cfp: prompt
        return "", str(error) or type(error).__name__


def main():
    hook_input = read_hook_input()
    prompt = hook_input.get("prompt", "") if isinstance(hook_input, dict) else ""
    if not isinstance(prompt, str) or not prompt.startswith("/cfp:"):
        return 0

    store, error = resolve_store()
    initialized = bool(store) and (Path(store) / "config.md").is_file()
    today = datetime.date.today().isoformat()

    lines = [
        "<cfp-context>",
        f"<plugin-root>{escape(str(PLUGIN_ROOT))}</plugin-root>",
        f"<store>{escape(store)}</store>",
        f"<store-initialized>{'true' if initialized else 'false'}</store-initialized>",
    ]
    if error is not None:
        lines.append(f"<store-error>{escape(error)}</store-error>")
    lines += [f"<today>{today}</today>", "</cfp-context>"]
    response = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": "\n".join(lines),
        }
    }
    print(json.dumps(response))
    return 0


if __name__ == "__main__":
    sys.exit(main())
