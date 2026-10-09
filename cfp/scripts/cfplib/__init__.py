"""cfplib: stdlib-only library behind cfp_store.py."""


class CfpError(Exception):
    """Domain error reported to the user as {"ok": false, "error": ...}."""
