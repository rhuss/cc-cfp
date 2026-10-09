"""Pre-flight rule check: evaluate the profile's hard rules against the store."""

import calendar
import datetime

from cfplib import CfpError, config, lifecycle, profile, proposals, talks, text as textutil

MANUAL_KINDS = ("vendor_pitch", "custom")
SEVERITIES = profile.SEVERITIES
AUDIENCE_RULE_SOURCE = "FR-029 audience level comparison"
# Gender values that mean "not known"; anything else that is not a man counts as not a man.
UNKNOWN_GENDERS = {"", "unknown", "n/a", "na", "?", "prefer not to say", "undisclosed", "none"}
MAN_GENDERS = {"man", "male", "m"}


def shift_months(date, months):
    """Move a date by a number of months, clamping the day to the month length."""
    month_index = date.month - 1 + months
    year = date.year + month_index // 12
    month = month_index % 12 + 1
    day = min(date.day, calendar.monthrange(year, month)[1])
    return datetime.date(year, month, day)


def _finding(rule, severity, text):
    return {
        "rule": rule.get("id"),
        "kind": rule.get("kind"),
        "severity": severity,
        "text": text,
        "source": rule.get("source") or "",
    }


def _normalize_gender(value):
    """Map a free-text gender to 'man', '' (unknown), or the lowercased value."""
    value = str(value or "").strip().lower()
    if value in UNKNOWN_GENDERS:
        return ""
    if value in MAN_GENDERS:
        return "man"
    return value


def _company(entry):
    entry = str(entry or "")
    if "," not in entry:
        return ""
    return entry.rsplit(",", 1)[1].strip()


class _Context:
    def __init__(self, store_path, proposal_id, today):
        self.store = store_path
        self.proposal_id = proposal_id
        self.today = textutil.parse_date(textutil.today_iso(today))
        self.path, self.meta, self.body = proposals.load_proposal(store_path, proposal_id)
        self.eff = proposals.effective_for(store_path, self.meta)
        self.texts = proposals.field_texts(self.body)
        self.config = config.load_store_config(store_path)
        self.session_type = next(
            (t for t in self.eff.get("session_types", []) if t.get("id") == self.meta.get("session_type")), None
        )
        self.total_speakers = 1 + len(self.meta.get("co_speakers") or [])
        self.problems = []


def _rule_submission_limit(ctx, rule):
    params = rule.get("params") or {}
    # FR-005: an event override's submission_limit wins over the family rule's params.max.
    event_limit = (ctx.eff.get("event") or {}).get("submission_limit")
    limit = event_limit if event_limit is not None else params.get("max", ctx.eff.get("submission_limit"))
    if limit is None:
        return None
    count, problems = lifecycle.count_submissions(ctx.store, ctx.meta.get("event"), exclude_proposal=ctx.proposal_id)
    ctx.problems.extend(problems)
    if count >= int(limit):
        return _finding(
            rule,
            rule.get("severity", "disqualify"),
            f"{count} proposals already count toward the limit of {limit} for {ctx.meta.get('event')} "
            f"(statuses submitted, accepted, rejected, presented); submitting this one would exceed it.",
        )
    if problems:
        skipped = ", ".join(p["path"] for p in problems)
        return _finding(
            rule,
            "warn",
            f"{count} proposals count toward the limit of {limit} for {ctx.meta.get('event')}, but "
            f"{len(problems)} proposal file(s) could not be read and were not counted: {skipped}.",
        )
    return None


def _rule_repeat(ctx, rule):
    params = rule.get("params") or {}
    months = int(params.get("months", 12))
    note_field = params.get("note_field", "previously_presented")
    window_start = shift_months(ctx.today, -months)
    try:
        talk = talks.show_talk(ctx.store, ctx.meta.get("talk"))
    except CfpError:
        return None
    hits = []
    for outing in talk.get("outings") or []:
        if not isinstance(outing, dict) or outing.get("kind", "presented") != "presented":
            continue
        if (outing.get("family") or "") != ctx.meta.get("profile"):
            continue
        date = textutil.parse_date(outing.get("date"))
        if date is None or date < window_start or date > ctx.today:
            continue
        hits.append(outing)
    if not hits:
        return None
    note = ctx.texts.get(note_field, "").strip()
    severity = "warn" if note else rule.get("severity", "disqualify")
    described = "; ".join(f"{h.get('event', '?')} on {h.get('date')}" for h in hits)
    text = f"Talk '{talk.get('title') or ctx.meta.get('talk')}' was presented within the last {months} months at {described}."
    if note:
        text += f" The '{note_field}' field explains the differences; make sure they are significant."
    else:
        text += f" Explain the significant differences in the '{note_field}' field, or the proposal is not selected."
    return _finding(rule, severity, text)


def _rule_track(ctx, rule):
    tracks = ctx.eff.get("tracks") or []
    if not tracks:
        return None
    track = str(ctx.meta.get("track") or "").strip()
    if track and track.lower() in {str(t).lower() for t in tracks}:
        return None
    shown = "no track chosen" if not track else f"track '{track}' is not in the event's list"
    return _finding(rule, rule.get("severity", "disqualify"), f"{shown}. Event tracks: {', '.join(tracks)}.")


def _rule_speaker_count(ctx, rule):
    if not ctx.session_type:
        return None
    low = ctx.session_type.get("min_speakers")
    high = ctx.session_type.get("max_speakers")
    total = ctx.total_speakers
    if (low is not None and total < int(low)) or (high is not None and total > int(high)):
        bounds = f"{low} to {high}" if low is not None and high is not None else (f"at least {low}" if low is not None else f"at most {high}")
        return _finding(
            rule,
            rule.get("severity", "disqualify"),
            f"{total} speakers (speaker plus {total - 1} co-speakers) but session type '{ctx.session_type.get('id')}' allows {bounds}.",
        )
    return None


def _rule_all_men(ctx, rule):
    params = rule.get("params") or {}
    if ctx.total_speakers < int(params.get("min_speakers", 3)):
        return None
    genders = [_normalize_gender(ctx.config.get("speaker_gender"))]
    co_genders = [_normalize_gender(g) for g in (ctx.meta.get("co_speaker_genders") or [])]
    co_genders += [""] * (ctx.total_speakers - 1 - len(co_genders))
    genders += co_genders[: ctx.total_speakers - 1]
    if any(g and g != "man" for g in genders):
        return None
    if all(g == "man" for g in genders):
        return _finding(rule, rule.get("severity", "disqualify"), f"All {ctx.total_speakers} speakers identify as men; this session composition is not accepted.")
    unknown = sum(1 for g in genders if not g)
    return _finding(
        rule,
        "warn",
        f"{unknown} of {ctx.total_speakers} speaker genders are unknown; confirm the session is not all men "
        "(set co_speaker_genders on the proposal and speaker_gender in config.md).",
    )


def _rule_multi_company(ctx, rule):
    if not ctx.session_type or int(ctx.session_type.get("min_speakers") or 1) < 3:
        return None
    companies = [str(ctx.config.get("speaker_company") or "").strip()]
    companies += [_company(c) for c in (ctx.meta.get("co_speakers") or [])]
    if any(not c for c in companies):
        return _finding(
            rule,
            "warn",
            "Some speaker companies are unknown; use \"Name, Company\" for co-speakers and set speaker_company in config.md "
            "so the panel company rule can be checked.",
        )
    lowered = {c.lower() for c in companies}
    if len(lowered) == 1:
        return _finding(rule, rule.get("severity", "disqualify"), f"All speakers are from {companies[0]}; panelists must represent more than one company.")
    return None


EVALUATORS = {
    "submission_limit": _rule_submission_limit,
    "repeat_within_months": _rule_repeat,
    "track_in_event": _rule_track,
    "speaker_count": _rule_speaker_count,
    "all_men_panel": _rule_all_men,
    "multi_company_panel": _rule_multi_company,
}


def _store_result(ctx, findings, today):
    ok = not any(f.get("severity") == "disqualify" for f in findings)
    ctx.meta["preflight"] = {"date": textutil.today_iso(today), "ok": ok, "findings": findings}
    proposals._save(ctx.path, ctx.meta, ctx.body, ctx.eff, today)
    return ok


def run(store_path, proposal_id, today=None):
    ctx = _Context(store_path, proposal_id, today)
    findings = []
    manual = []
    for rule in ctx.eff.get("rules") or []:
        if not isinstance(rule, dict):
            continue
        kind = rule.get("kind")
        if kind in MANUAL_KINDS:
            manual.append({"rule": rule.get("id"), "kind": kind, "text": rule.get("text", ""), "source": rule.get("source") or ""})
            continue
        evaluator = EVALUATORS.get(kind)
        if evaluator is None:
            continue
        finding = evaluator(ctx, rule)
        if finding:
            findings.append(finding)
    ok = _store_result(ctx, findings, today)
    return {"ok": ok, "findings": findings, "manual": manual, "problems": ctx.problems}


def add_finding(store_path, proposal_id, rule, severity, text, source="", today=None):
    if severity not in SEVERITIES:
        raise CfpError(f"severity must be one of {', '.join(SEVERITIES)}")
    rule = str(rule or "").strip()
    text = str(text or "").strip()
    if not rule or not text:
        raise CfpError("a finding needs a rule id and a text")
    ctx = _Context(store_path, proposal_id, today)
    findings = list((ctx.meta.get("preflight") or {}).get("findings") or [])
    findings.append(
        {
            "rule": rule,
            "kind": "manual",
            "severity": severity,
            "text": text,
            "source": source or (AUDIENCE_RULE_SOURCE if rule == "audience-level" else ""),
        }
    )
    ok = _store_result(ctx, findings, today)
    return {"ok": ok, "findings": findings}
