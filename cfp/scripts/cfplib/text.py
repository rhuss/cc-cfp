"""Text normalization and character counting shared by bios, proposals, counts."""

import datetime


def normalize(text):
    """CRLF to LF, strip leading and trailing whitespace."""
    if text is None:
        return ""
    return str(text).replace("\r\n", "\n").replace("\r", "\n").strip()


def count_chars(text):
    """Unicode code points of the normalized text (so a sharp s or an emoji count as 1)."""
    return len(normalize(text))


def coerce_limit(value):
    """Return a positive int limit, or None when the value is empty or not usable.

    Hand-edited profiles can carry limits like ``"75"`` or ``"n/a"``; those must
    not crash counting, so anything that is not a positive integer counts as
    "no limit" (``profile validate`` reports the problem).
    """
    if value is None or isinstance(value, bool):
        return None
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def limit_status(chars, limit, verification):
    """Return ok, over, unverified, or no-limit for a count against a limit."""
    if limit is None:
        return "no-limit"
    if chars > limit:
        return "over"
    if (verification or "unverified") == "unverified":
        return "unverified"
    return "ok"


def limit_result(chars, limit, verification):
    """The count-against-limit dict every field and bio report shares."""
    return {
        "chars": chars,
        "limit": limit,
        "limit_status": (verification or "unverified") if limit is not None else None,
        "status": limit_status(chars, limit, verification),
    }


def today_iso(today=None):
    if today:
        return str(today)
    return datetime.date.today().isoformat()


def parse_date(value):
    if value is None or value == "":
        return None
    if isinstance(value, datetime.date):
        return value
    try:
        return datetime.date.fromisoformat(str(value))
    except ValueError:
        return None
