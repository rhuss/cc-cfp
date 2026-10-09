#!/usr/bin/env python3
"""UserPromptSubmit hook for the cfp plugin.

Reads the hook input JSON from stdin and, when the prompt starts with
``/cfp:``, emits an ``additionalContext`` block that tells the skills where
the plugin lives, where the store is, and whether the store is initialized.

The hook never exits non-zero for a ``/cfp:`` prompt: a missing or broken
user configuration simply yields an empty store path.
"""

import datetime
import json
import os
import sys
from pathlib import Path


def read_hook_input():
    try:
        return json.loads(sys.stdin.read() or "{}")
    except (json.JSONDecodeError, ValueError):
        return {}


def resolve_store():
    """Return the store path from env CFP_STORE or the user config file."""
    env_store = os.environ.get("CFP_STORE", "").strip()
    if env_store:
        return env_store
    config_path = Path.home() / ".config" / "cc-cfp" / "config.json"
    try:
        with open(config_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return ""
    if not isinstance(data, dict):
        return ""
    store = data.get("store", "")
    return store if isinstance(store, str) else ""


def main():
    hook_input = read_hook_input()
    prompt = hook_input.get("prompt", "") if isinstance(hook_input, dict) else ""
    if not isinstance(prompt, str) or not prompt.startswith("/cfp:"):
        return 0

    # hooks/scripts/context-hook.py -> hooks/scripts -> hooks -> plugin root
    plugin_root = Path(__file__).resolve().parent.parent.parent
    store = resolve_store()
    initialized = bool(store) and (Path(store).expanduser() / "config.md").is_file()
    today = datetime.date.today().isoformat()

    context = (
        "<cfp-context>\n"
        f"<plugin-root>{plugin_root}</plugin-root>\n"
        f"<store>{store}</store>\n"
        f"<store-initialized>{'true' if initialized else 'false'}</store-initialized>\n"
        f"<today>{today}</today>\n"
        "</cfp-context>"
    )
    response = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context,
        }
    }
    print(json.dumps(response))
    return 0


if __name__ == "__main__":
    sys.exit(main())
