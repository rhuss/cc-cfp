#!/usr/bin/env python3
"""cfp_store.py: single CLI entry point for the cfp plugin store.

Invoked as ``python3 -I cfp_store.py <group> <subcommand> [options]`` for most
operations; ``count``, ``pasteview``, and ``preflight`` take ``--proposal``
directly. Every invocation prints exactly one JSON object on stdout (except
``pasteview --format markdown``). Success has ``"ok": true``; domain errors
have ``"ok": false, "error": ...`` and exit code 1; usage errors exit 2.
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cfplib import (  # noqa: E402
    CfpError,
    bios,
    config,
    counts,
    lifecycle,
    pasteview,
    paths,
    preflight,
    profile,
    proposals,
    review,
    seeds,
    talks,
)
from cfplib import text as textutil  # noqa: E402


class UsageError(Exception):
    pass


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise UsageError(f"usage error: {message}")


def read_json_file(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        raise CfpError(f"JSON file not found: {path}")
    except OSError as error:
        raise CfpError(f"cannot read JSON file {path}: {error.strerror or error}")
    except ValueError as error:
        raise CfpError(f"invalid JSON in {path}: {error}")


def read_text_file(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except FileNotFoundError:
        raise CfpError(f"text file not found: {path}")
    except UnicodeDecodeError as error:
        raise CfpError(f"text file {path} is not valid UTF-8: {error.reason}")
    except OSError as error:
        raise CfpError(f"cannot read text file {path}: {error.strerror or error}")


def emit(payload, code=0):
    print(json.dumps(payload, ensure_ascii=False))
    return code


# ---------------------------------------------------------------- parser


def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--store", default=argparse.SUPPRESS, help="store path (overrides CFP_STORE and the user config)")
    common.add_argument("--today", default=argparse.SUPPRESS, help="ISO date used instead of the current date")

    parser = JsonArgumentParser(prog="cfp_store.py", parents=[common], description=__doc__)
    groups = parser.add_subparsers(dest="group")

    def group(name, help_text):
        g = groups.add_parser(name, help=help_text, parents=[common])
        return g.add_subparsers(dest="command")

    def sub(subparsers, name, func, help_text=""):
        p = subparsers.add_parser(name, help=help_text, parents=[common])
        p.set_defaults(func=func)
        return p

    # config
    g = group("config", "store configuration")
    sub(g, "show", cmd_config_show)
    p = sub(g, "init", cmd_config_init)
    p.add_argument("--speaker-name", required=True)
    p.add_argument("--speaker-company", default=None)
    p.add_argument("--voice-profile", default=None)
    p.add_argument("--review-rounds", type=int, default=None)
    p.add_argument("--default-profile", default=None)
    p.add_argument("--seed-dir", default=None)
    p.add_argument("--user-seed-dir", default=None, help=argparse.SUPPRESS)
    p = sub(g, "set", cmd_config_set)
    p.add_argument("--key", required=True)
    p.add_argument("--value", required=True)

    # profile
    g = group("profile", "conference profiles")
    sub(g, "list", cmd_profile_list)
    p = sub(g, "show", cmd_profile_show)
    p.add_argument("--profile", required=True)
    p.add_argument("--event", default=None)
    p = sub(g, "validate", cmd_profile_validate)
    p.add_argument("--profile", required=True)
    p.add_argument("--event", default=None)
    p = sub(g, "write", cmd_profile_write)
    p.add_argument("--profile", required=True)
    p.add_argument("--from-json", required=True)
    p = sub(g, "approve", cmd_profile_approve)
    p.add_argument("--profile", required=True)
    p.add_argument("--event", default=None)
    p.add_argument("--revoke", action="store_true")
    p = sub(g, "seed-status", cmd_profile_seed_status, "compare the shipped and personal seed profiles with the store")
    p.add_argument("--seed-dir", required=True)
    p.add_argument("--user-seed-dir", default=None, help=argparse.SUPPRESS)
    p = sub(g, "seed-update", cmd_profile_seed_update, "replace an outdated store profile with its seed")
    p.add_argument("--profile", required=True)
    p.add_argument("--seed-dir", required=True)
    p.add_argument("--user-seed-dir", default=None, help=argparse.SUPPRESS)
    choice = p.add_mutually_exclusive_group()
    choice.add_argument(
        "--files", default=None,
        help="comma-separated shipped files to take besides profile.md (paths as seed-status prints them)",
    )
    choice.add_argument("--all", action="store_true", help="take every changed or missing shipped file")

    # event
    g = group("event", "event overrides")
    p = sub(g, "write", cmd_event_write)
    p.add_argument("--profile", required=True)
    p.add_argument("--event", required=True)
    p.add_argument("--from-json", required=True)
    p = sub(g, "list", cmd_event_list)
    p.add_argument("--profile", required=True)

    # example
    g = group("example", "calibration examples")
    p = sub(g, "add", cmd_example_add)
    p.add_argument("--profile", required=True)
    p.add_argument("--from-json", required=True)
    p = sub(g, "list", cmd_example_list)
    p.add_argument("--profile", required=True)
    p.add_argument("--limit", type=int, default=None)

    # bio
    g = group("bio", "bio variations")
    sub(g, "list", cmd_bio_list)
    p = sub(g, "show", cmd_bio_show)
    p.add_argument("--name", required=True)
    p = sub(g, "write", cmd_bio_write)
    p.add_argument("--name", required=True)
    p.add_argument("--emphasis", default=None)
    p.add_argument("--target-length", type=int, default=None)
    p.add_argument("--text-file", required=True)
    p = sub(g, "delete", cmd_bio_delete)
    p.add_argument("--name", required=True)

    # resource
    g = group("resource", "speaker resources")
    p = sub(g, "list", cmd_resource_list)
    p.add_argument("--type", default=None)
    p = sub(g, "write", cmd_resource_write)
    p.add_argument("--from-json", required=True)
    p = sub(g, "delete", cmd_resource_delete)
    p.add_argument("--id", required=True)

    # talk
    g = group("talk", "talk stories")
    p = sub(g, "list", cmd_talk_list)
    p.add_argument("--status", default=None)
    p = sub(g, "show", cmd_talk_show)
    p.add_argument("--talk", required=True)
    p = sub(g, "write", cmd_talk_write)
    p.add_argument("--talk", default=None)
    p.add_argument("--from-json", required=True)
    p = sub(g, "complete", cmd_talk_complete)
    p.add_argument("--talk", required=True)

    # proposal
    g = group("proposal", "proposals")
    p = sub(g, "list", cmd_proposal_list)
    p.add_argument("--status", default=None)
    p.add_argument("--event", default=None)
    p.add_argument("--talk", default=None)
    p = sub(g, "show", cmd_proposal_show)
    p.add_argument("--proposal", required=True)
    p = sub(g, "create", cmd_proposal_create)
    p.add_argument("--talk", required=True)
    p.add_argument("--profile", required=True)
    p.add_argument("--event", required=True)
    p.add_argument("--session-type", required=True)
    p.add_argument("--angle", default=None)
    p = sub(g, "set-field", cmd_proposal_set_field)
    p.add_argument("--proposal", required=True)
    p.add_argument("--field", required=True)
    p.add_argument("--text-file", required=True)
    p = sub(g, "set-meta", cmd_proposal_set_meta)
    p.add_argument("--proposal", required=True)
    p.add_argument("--from-json", default=None, help="JSON object with any of the keys below (flags win over the file)")
    p.add_argument("--track", default=None)
    p.add_argument("--audience-level", default=None)
    p.add_argument("--bio", default=None)
    p.add_argument("--resources", default=None, help="comma-separated resource ids (empty string clears)")
    p.add_argument("--co-speakers", default=None, help='JSON list, for example ["Name, Company"]')
    p.add_argument("--co-speaker-genders", default=None, help="JSON list of strings")
    p.add_argument("--angle", default=None)
    p.add_argument("--session-type", default=None)
    p = sub(g, "set-bio-text", cmd_proposal_set_bio_text)
    p.add_argument("--proposal", required=True)
    p.add_argument("--text-file", required=True)
    p = sub(g, "mark-voice-pass", cmd_proposal_mark_voice_pass)
    p.add_argument("--proposal", required=True)

    # count and pasteview (no group)
    p = sub(groups, "count", cmd_count, "character counts against limits")
    p.add_argument("--proposal", required=True)
    p = sub(groups, "pasteview", cmd_pasteview, "fields in form order with counts")
    p.add_argument("--proposal", required=True)
    p.add_argument("--format", default="json", choices=["markdown", "json"])

    # review
    g = group("review", "committee review rounds")
    p = sub(g, "packet", cmd_review_packet)
    p.add_argument("--proposal", required=True)
    p.add_argument("--examples", type=int, default=3)
    p = sub(g, "record", cmd_review_record)
    p.add_argument("--proposal", required=True)
    p.add_argument("--from-json", required=True)
    p = sub(g, "history", cmd_review_history)
    p.add_argument("--proposal", required=True)

    # preflight: `preflight --proposal` and `preflight add-finding ...`
    pf = groups.add_parser("preflight", help="hard rule check", parents=[common])
    pf.add_argument("--proposal", default=None)
    pf.set_defaults(func=cmd_preflight)
    pf_sub = pf.add_subparsers(dest="command")
    p = pf_sub.add_parser("add-finding", parents=[common])
    p.set_defaults(func=cmd_preflight_add_finding)
    p.add_argument("--proposal", required=True)
    p.add_argument("--from-json", default=None, help="JSON object with rule, severity, text, source (flags win)")
    p.add_argument("--rule", default=None)
    p.add_argument(
        "--severity", default=None, choices=list(preflight.SEVERITIES),
        help="optional for a rule id of the profile (the rule's severity applies), required otherwise",
    )
    p.add_argument("--text", default=None)
    p.add_argument("--source", default=None)

    # status
    g = group("status", "proposal lifecycle")
    p = sub(g, "set", cmd_status_set)
    p.add_argument("--proposal", required=True)
    p.add_argument("--to", required=True)
    p.add_argument("--date", default=None)
    p.add_argument("--force", action="store_true")
    p = sub(g, "ready-check", cmd_status_ready_check)
    p.add_argument("--proposal", required=True)

    return parser


# ---------------------------------------------------------------- helpers


def ctx_store(args):
    return config.require_store(config.resolve_store(getattr(args, "store", None)))


def ctx_today(args):
    today = getattr(args, "today", None)
    if today and textutil.parse_date(today) is None:
        raise UsageError(f"usage error: --today must be an ISO date (YYYY-MM-DD), got {today!r}")
    return textutil.today_iso(today)


# ---------------------------------------------------------------- config


def cmd_config_show(args):
    store, source = config.resolve_store_with_source(getattr(args, "store", None))
    data_dir = paths.data_dir()  # an invalid CFP_DATA_DIR fails here, even when the store came from elsewhere
    _, read_path = paths.read_config()
    exists = config.store_config_path(store).is_file()
    cfg = config.load_store_config(store) if exists else dict(config.DEFAULT_STORE_CONFIG)
    return {
        "store": str(store),
        "store_source": source,
        "exists": exists,
        "config": cfg,
        "config_file": str(read_path) if read_path else None,
        "config_write_path": str(paths.config_file()),
        "data_dir": str(data_dir),
        "user_profiles_dir": str(paths.user_profiles_dir()),
    }


def _cfp_store_warning(store):
    """Warn when CFP_STORE names another store than the one being saved.

    Paths are compared after ``~`` expansion and resolution. A relative
    CFP_STORE (an error for later commands) also differs, so it warns too.
    """
    raw = os.environ.get("CFP_STORE", "").strip()
    if not raw:
        return []
    try:
        if paths.env_store().resolve() == Path(store):
            return []
    except CfpError:
        pass
    return [f"CFP_STORE is set to '{raw}' and overrides the saved store '{store}' in later sessions"]


def user_seed_dir(args):
    """The personal profiles folder: ``--user-seed-dir`` (tests) or ``<data folder>/profiles``."""
    explicit = getattr(args, "user_seed_dir", None)
    return Path(explicit) if explicit else paths.user_profiles_dir()


def cmd_config_init(args):
    # Fail on an invalid CFP_DATA_DIR or CFP_CONFIG_DIR before anything is written.
    user_profiles_dir = user_seed_dir(args)
    paths.config_file()
    store = config.resolve_store(getattr(args, "store", None))
    values = {
        "speaker_name": args.speaker_name,
        "speaker_company": args.speaker_company,
        "voice_profile": args.voice_profile,
        "review_rounds": args.review_rounds,
        "default_profile": args.default_profile,
    }
    result = config.init_store(store, values, seed_dir=args.seed_dir, user_seed_dir=user_profiles_dir)
    result["warnings"] = result["warnings"] + _cfp_store_warning(Path(result["store"]))
    result["user_profiles_dir"] = str(user_profiles_dir)
    return result


def cmd_config_set(args):
    store = ctx_store(args)
    value = config.set_store_config(store, args.key, args.value)
    return {"key": args.key, "value": value}


# ---------------------------------------------------------------- profile


def cmd_profile_list(args):
    profiles, problems = profile.list_profiles(ctx_store(args), today=ctx_today(args))
    return {"profiles": profiles, "problems": problems}


def cmd_profile_show(args):
    store = ctx_store(args)
    eff = profile.load_effective(store, args.profile, args.event)
    if eff["event"]:
        eff["event"]["days_to_close"] = profile.days_to_close(eff["event"], ctx_today(args))
    return eff


def cmd_profile_validate(args):
    problems = profile.validate(ctx_store(args), args.profile, args.event)
    return {"valid": not problems, "problems": problems}


def cmd_profile_write(args):
    path = profile.write_profile_from_json(ctx_store(args), args.profile, read_json_file(args.from_json))
    return {"path": str(path)}


def cmd_profile_approve(args):
    return profile.approve(ctx_store(args), args.profile, event_id=args.event, approved=not args.revoke)


def cmd_profile_seed_status(args):
    user_dir = user_seed_dir(args)
    listing, warnings = seeds.status_report(ctx_store(args), args.seed_dir, user_dir)
    return {"seeds": listing, "warnings": warnings}


def cmd_profile_seed_update(args):
    user_dir = user_seed_dir(args)
    files = [part.strip() for part in (args.files or "").split(",") if part.strip()]
    return seeds.update(
        ctx_store(args), args.seed_dir, args.profile, files=files, all_files=args.all, user_dir=user_dir
    )


def cmd_event_write(args):
    path = profile.write_event_from_json(ctx_store(args), args.profile, args.event, read_json_file(args.from_json))
    return {"path": str(path)}


def cmd_event_list(args):
    events, problems = profile.list_events(ctx_store(args), args.profile, today=ctx_today(args))
    return {"events": events, "problems": problems}


def cmd_example_add(args):
    path = profile.add_example(ctx_store(args), args.profile, read_json_file(args.from_json), today=ctx_today(args))
    return {"path": str(path)}


def cmd_example_list(args):
    examples, problems = profile.list_examples(ctx_store(args), args.profile, limit=args.limit)
    return {"examples": examples, "problems": problems}


# ---------------------------------------------------------------- bio and resource


def cmd_bio_list(args):
    listing, problems = bios.list_bios(ctx_store(args))
    return {"bios": listing, "problems": problems}


def cmd_bio_show(args):
    return bios.show_bio(ctx_store(args), args.name)


def cmd_bio_write(args):
    return bios.write_bio(
        ctx_store(args), args.name, args.emphasis, args.target_length, read_text_file(args.text_file), today=ctx_today(args)
    )


def cmd_bio_delete(args):
    return bios.delete_bio(ctx_store(args), args.name)


def cmd_resource_list(args):
    listing, problems = bios.list_resources(ctx_store(args), kind=args.type)
    return {"resources": listing, "problems": problems}


def cmd_resource_write(args):
    return bios.write_resource(ctx_store(args), read_json_file(args.from_json))


def cmd_resource_delete(args):
    return bios.delete_resource(ctx_store(args), args.id)


# ---------------------------------------------------------------- talk


def cmd_talk_list(args):
    listing, problems = talks.list_talks(ctx_store(args), status=args.status)
    return {"talks": listing, "problems": problems}


def cmd_talk_show(args):
    return talks.show_talk(ctx_store(args), args.talk)


def cmd_talk_write(args):
    return talks.write_talk(ctx_store(args), args.talk, read_json_file(args.from_json), today=ctx_today(args))


def cmd_talk_complete(args):
    return talks.complete_talk(ctx_store(args), args.talk)


# ---------------------------------------------------------------- proposal


def parse_json_arg(value, name):
    if value is None:
        return None
    try:
        return json.loads(value)
    except ValueError as error:
        raise UsageError(f"usage error: --{name} must be JSON: {error}")


def cmd_proposal_list(args):
    listing, problems = proposals.list_proposals(ctx_store(args), status=args.status, event=args.event, talk=args.talk)
    return {"proposals": listing, "problems": problems}


def cmd_proposal_show(args):
    return proposals.show(ctx_store(args), args.proposal)


def cmd_proposal_create(args):
    return proposals.create(
        ctx_store(args), args.talk, args.profile, args.event, args.session_type, angle=args.angle, today=ctx_today(args)
    )


def cmd_proposal_set_field(args):
    return proposals.set_field(ctx_store(args), args.proposal, args.field, read_text_file(args.text_file), today=ctx_today(args))


SET_META_KEYS = ("track", "audience_level", "bio", "resources", "co_speakers", "co_speaker_genders", "angle", "session_type")


def _json_object_arg(path, allowed_keys):
    """Read an optional JSON object (free text goes through files, not shell args)."""
    if not path:
        return {}
    data = read_json_file(path)
    if not isinstance(data, dict):
        raise CfpError(f"{path} must contain a JSON object")
    unknown = sorted(set(data) - set(allowed_keys))
    if unknown:
        raise CfpError(f"unknown keys in {path}: {', '.join(unknown)}; allowed: {', '.join(allowed_keys)}")
    return data


def cmd_proposal_set_meta(args):
    values = _json_object_arg(args.from_json, SET_META_KEYS)
    resources = values.get("resources")
    if args.resources is not None:
        resources = [r.strip() for r in args.resources.split(",") if r.strip()]
    elif isinstance(resources, str):
        resources = [r.strip() for r in resources.split(",") if r.strip()]
    co_speakers = parse_json_arg(args.co_speakers, "co-speakers")
    co_speaker_genders = parse_json_arg(args.co_speaker_genders, "co-speaker-genders")
    return proposals.set_meta(
        ctx_store(args),
        args.proposal,
        track=args.track if args.track is not None else values.get("track"),
        audience_level=args.audience_level if args.audience_level is not None else values.get("audience_level"),
        bio=args.bio if args.bio is not None else values.get("bio"),
        resources=resources,
        co_speakers=co_speakers if co_speakers is not None else values.get("co_speakers"),
        co_speaker_genders=co_speaker_genders if co_speaker_genders is not None else values.get("co_speaker_genders"),
        angle=args.angle if args.angle is not None else values.get("angle"),
        session_type=args.session_type if args.session_type is not None else values.get("session_type"),
        today=ctx_today(args),
    )


def cmd_proposal_set_bio_text(args):
    return proposals.set_bio_text(ctx_store(args), args.proposal, read_text_file(args.text_file), today=ctx_today(args))


def cmd_proposal_mark_voice_pass(args):
    return proposals.mark_voice_pass(ctx_store(args), args.proposal, today=ctx_today(args))


# ---------------------------------------------------------------- count and pasteview


def cmd_count(args):
    return counts.count_proposal(ctx_store(args), args.proposal)


def cmd_pasteview(args):
    result = pasteview.render(ctx_store(args), args.proposal, args.format)
    if args.format == "markdown":
        sys.stdout.write(result)
        return None
    return result


# ---------------------------------------------------------------- review and preflight


def cmd_review_packet(args):
    return review.packet(ctx_store(args), args.proposal, examples=args.examples)


def cmd_review_record(args):
    return review.record(ctx_store(args), args.proposal, read_json_file(args.from_json), today=ctx_today(args))


def cmd_review_history(args):
    return review.history(ctx_store(args), args.proposal)


def _preflight_payload(result):
    # The CLI "ok" key means the call succeeded; the rule verdict is reported as "passed".
    payload = dict(result)
    payload["passed"] = payload.pop("ok")
    return payload


def cmd_preflight(args):
    if not getattr(args, "proposal", None):
        raise UsageError("usage error: preflight needs --proposal <id>")
    return _preflight_payload(preflight.run(ctx_store(args), args.proposal, today=ctx_today(args)))


def cmd_preflight_add_finding(args):
    values = _json_object_arg(args.from_json, ("rule", "severity", "text", "source"))
    rule = args.rule if args.rule is not None else values.get("rule")
    severity = args.severity if args.severity is not None else values.get("severity")
    text = args.text if args.text is not None else values.get("text")
    source = args.source if args.source is not None else values.get("source", "")
    if not rule or not text:
        raise UsageError(
            "usage error: add-finding needs --rule and --text (flags or --from-json); "
            "--severity is optional for a rule id of the profile"
        )
    if severity and severity not in preflight.SEVERITIES:
        raise UsageError(f"usage error: severity must be {' or '.join(preflight.SEVERITIES)}, got {severity!r}")
    return _preflight_payload(
        preflight.add_finding(ctx_store(args), args.proposal, rule, severity, text, source=source or "", today=ctx_today(args))
    )


# ---------------------------------------------------------------- status


def cmd_status_set(args):
    return lifecycle.set_status(
        ctx_store(args), args.proposal, args.to, date=args.date, force=args.force, today=ctx_today(args)
    )


def cmd_status_ready_check(args):
    return lifecycle.ready_check(ctx_store(args), args.proposal)


# ---------------------------------------------------------------- main


def main(argv=None):
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        if not getattr(args, "func", None):
            raise UsageError("usage error: a subcommand is required (see --help)")
        result = args.func(args)
    except UsageError as error:
        return emit({"ok": False, "error": str(error)}, 2)
    except CfpError as error:
        return emit({"ok": False, "error": str(error)}, 1)
    except Exception as error:  # noqa: BLE001  keep the one-JSON-object contract on unexpected failures
        return emit({"ok": False, "error": f"internal error ({type(error).__name__}): {error}"}, 1)
    if result is None:
        return 0  # subcommand wrote its own output (markdown paste view)
    payload = {"ok": True}
    payload.update(result)
    return emit(payload, 0)


if __name__ == "__main__":
    sys.exit(main())
