"""Tests for hard rule evaluation (cfplib.preflight), one rule kind at a time."""

import pytest

from cfplib import CfpError, config, frontmatter, lifecycle, preflight, proposals, store, talks

TODAY = "2026-10-09"
EVENT = "kubecon-eu-2027"
LF_URL = "https://events.linuxfoundation.org/kubecon-cloudnativecon-europe/program/cfp/"


def make(s, talk_id="t", event=EVENT, session_type="session", status="draft", **meta):
    if not store.talk_path(s, talk_id).is_file():
        talks.write_talk(s, talk_id, {"title": talk_id.upper()}, today=TODAY)
    pid = proposals.create(s, talk_id, "kubecon", event, session_type, today=TODAY)["id"]
    proposals.set_field(s, pid, "track", "Security", today=TODAY)
    if status != "draft" or meta:
        path = store.proposal_path(s, pid)
        m, body = store.load(path)
        m["status"] = status
        m.update(meta)
        store.save(path, m, body)
    return pid


def findings_by_rule(result):
    return {f["rule"]: f for f in result["findings"]}


def test_clean_proposal_has_no_findings_and_lists_manual_rules(seeded_store):
    pid = make(seeded_store)
    result = preflight.run(seeded_store, pid, today=TODAY)
    assert result["ok"] is True and result["findings"] == []
    assert [m["rule"] for m in result["manual"]] == ["vendor-pitch"]
    assert result["manual"][0]["kind"] == "vendor_pitch" and "pitch" in result["manual"][0]["text"]
    stored = proposals.show(seeded_store, pid)["preflight"]
    assert stored["ok"] is True and stored["findings"] == [] and stored["date"] == TODAY


def test_submission_limit_counts_by_status_excluding_self(seeded_store):
    s = seeded_store
    for n, status in enumerate(["submitted", "accepted", "rejected"]):
        make(s, f"s{n}", status=status)
    make(s, "d0", status="draft")
    make(s, "w0", status="withdrawn")
    make(s, "other", event="kubecon-na-2026", status="submitted")
    pid = make(s, "fourth")
    result = preflight.run(s, pid, today=TODAY)
    assert result["ok"] is False
    finding = findings_by_rule(result)["submission-limit"]
    assert finding["kind"] == "submission_limit" and finding["severity"] == "disqualify"
    assert finding["source"] == LF_URL and "3" in finding["text"]

    # a proposal that is itself submitted does not count against itself:
    # with two others counted plus this one submitted, there is no finding
    store_path = store.proposal_path(s, pid)
    meta, body = store.load(store_path)
    meta["status"] = "submitted"
    store.save(store_path, meta, body)
    path = store.proposal_path(s, "kubecon-eu-2027--s2")
    meta, body = store.load(path)
    meta["status"] = "withdrawn"
    store.save(path, meta, body)
    assert "submission-limit" not in findings_by_rule(preflight.run(s, pid, today=TODAY))


def test_submission_limit_warns_about_unreadable_proposal_files(seeded_store):
    s = seeded_store
    make(s, "s0", status="submitted")
    pid = make(s, "next")
    broken = store.proposal_path(s, "kubecon-eu-2027--broken")
    broken.write_text("---\nstatus: submitted\nevent: kubecon-eu-2027\n  bad: indent\n---\n")
    result = preflight.run(s, pid, today=TODAY)
    assert result["ok"] is True
    assert len(result["problems"]) == 1 and result["problems"][0]["path"] == str(broken)
    finding = findings_by_rule(result)["submission-limit"]
    assert finding["severity"] == "warn" and "could not be read" in finding["text"] and str(broken) in finding["text"]


def test_event_override_submission_limit_wins_over_family_rule(seeded_store):
    s = seeded_store
    make(s, "s0", status="submitted")
    pid = make(s, "second")
    assert "submission-limit" not in findings_by_rule(preflight.run(s, pid, today=TODAY))
    path = store.event_path(s, "kubecon", EVENT)
    meta, body = frontmatter.load(path)
    meta["submission_limit"] = 1  # a co-located edition with a tighter limit (FR-005)
    frontmatter.save(path, meta, body)
    finding = findings_by_rule(preflight.run(s, pid, today=TODAY))["submission-limit"]
    assert finding["severity"] == "disqualify" and "limit of 1" in finding["text"]


def set_outings(s, talk_id, outings):
    path = store.talk_path(s, talk_id)
    meta, body = store.load(path)
    meta["outings"] = outings
    store.save(path, meta, body)


def test_repeat_within_months_window_and_boundaries(seeded_store):
    s = seeded_store
    pid = make(s, "rep")
    outing = {"event": "KubeCon EU 2026", "family": "kubecon", "date": "2026-03-25", "link": "", "kind": "presented"}
    set_outings(s, "rep", [outing])
    result = preflight.run(s, pid, today=TODAY)
    finding = findings_by_rule(result)["repeat-one-year"]
    assert finding["severity"] == "disqualify" and result["ok"] is False
    assert "2026-03-25" in finding["text"] and finding["source"] == LF_URL

    set_outings(s, "rep", [dict(outing, date="2025-10-09")])  # exactly 12 months before today: inside
    assert "repeat-one-year" in findings_by_rule(preflight.run(s, pid, today=TODAY))
    set_outings(s, "rep", [dict(outing, date="2025-10-08")])  # one day earlier: outside
    assert "repeat-one-year" not in findings_by_rule(preflight.run(s, pid, today=TODAY))

    set_outings(s, "rep", [dict(outing, kind="submitted")])
    assert "repeat-one-year" not in findings_by_rule(preflight.run(s, pid, today=TODAY))
    set_outings(s, "rep", [dict(outing, family="pycon")])
    assert "repeat-one-year" not in findings_by_rule(preflight.run(s, pid, today=TODAY))


def test_repeat_ignores_future_outings(seeded_store):
    s = seeded_store
    pid = make(s, "rep")
    set_outings(s, "rep", [{"event": "KubeCon NA 2026", "family": "kubecon", "date": "2026-11-11", "link": "", "kind": "presented"}])
    assert "repeat-one-year" not in findings_by_rule(preflight.run(s, pid, today=TODAY))


def test_rejected_proposal_is_not_a_presentation(seeded_store):
    from cfplib import lifecycle

    s = seeded_store
    earlier = make(s, "rep", event="kubecon-na-2026", status="submitted")
    lifecycle.set_status(s, earlier, "rejected", date="2026-04-01", today=TODAY)
    assert talks.show_talk(s, "rep")["outings"] == []
    pid = make(s, "rep")
    result = preflight.run(s, pid, today=TODAY)
    assert "repeat-one-year" not in findings_by_rule(result) and result["ok"] is True


def test_shift_months_clamps_to_month_length():
    import datetime

    assert preflight.shift_months(datetime.date(2026, 3, 31), -1) == datetime.date(2026, 2, 28)
    assert preflight.shift_months(datetime.date(2024, 1, 31), 1) == datetime.date(2024, 2, 29)
    assert preflight.shift_months(datetime.date(2026, 1, 15), -12) == datetime.date(2025, 1, 15)
    assert preflight.shift_months(datetime.date(2026, 1, 10), -3) == datetime.date(2025, 10, 10)
    assert preflight.shift_months(datetime.date(2026, 10, 9), 0) == datetime.date(2026, 10, 9)


def test_repeat_downgraded_to_warn_with_previously_presented_note(seeded_store):
    s = seeded_store
    pid = make(s, "rep")
    set_outings(s, "rep", [{"event": "KubeCon EU 2026", "family": "kubecon", "date": "2026-03-25", "link": "", "kind": "presented"}])
    proposals.set_field(s, pid, "previously_presented", "Given at KubeCon EU 2026; this version adds production data.", today=TODAY)
    result = preflight.run(s, pid, today=TODAY)
    finding = findings_by_rule(result)["repeat-one-year"]
    assert finding["severity"] == "warn" and result["ok"] is True


def test_track_in_event_case_insensitive(seeded_store):
    s = seeded_store
    pid = make(s)
    path = store.proposal_path(s, pid)
    meta, body = store.load(path)
    meta["track"] = "security"
    store.save(path, meta, body)
    assert "track-in-event" not in findings_by_rule(preflight.run(s, pid, today=TODAY))
    meta["track"] = "Not A Track"
    store.save(path, meta, body)
    result = preflight.run(s, pid, today=TODAY)
    finding = findings_by_rule(result)["track-in-event"]
    assert finding["severity"] == "disqualify" and "Agentic AI" in finding["text"] and result["ok"] is False
    assert finding["source"] == LF_URL.replace("cfp/", "submission-reviewer-guidelines/")
    meta["track"] = None
    store.save(path, meta, body)
    assert "track-in-event" in findings_by_rule(preflight.run(s, pid, today=TODAY))


def test_track_rule_is_silent_when_event_has_no_tracks(seeded_store):
    s = seeded_store
    pid = make(s)
    path = store.proposal_path(s, pid)
    meta, body = store.load(path)
    meta["track"] = "Not A Track"
    store.save(path, meta, body)
    assert "track-in-event" in findings_by_rule(preflight.run(s, pid, today=TODAY))
    event_path = store.event_path(s, "kubecon", EVENT)
    event_meta, event_body = frontmatter.load(event_path)
    event_meta["tracks"] = []
    frontmatter.save(event_path, event_meta, event_body)
    result = preflight.run(s, pid, today=TODAY)
    assert "track-in-event" not in findings_by_rule(result) and result["ok"] is True


def test_speaker_count(seeded_store):
    s = seeded_store
    pid = make(s, "sc", co_speakers=["A, X", "B, Y"])
    finding = findings_by_rule(preflight.run(s, pid, today=TODAY))["speaker-count"]
    assert finding["severity"] == "disqualify" and "3" in finding["text"] and "2" in finding["text"]
    assert finding["source"] == LF_URL
    solo_panel = make(s, "panel", session_type="panel")
    finding = findings_by_rule(preflight.run(s, solo_panel, today=TODAY))["speaker-count"]
    assert "1" in finding["text"] and "3" in finding["text"]
    fine = make(s, "duo", co_speakers=["A, X"])
    assert "speaker-count" not in findings_by_rule(preflight.run(s, fine, today=TODAY))


def test_all_men_panel(seeded_store):
    s = seeded_store
    pid = make(s, "p", session_type="panel", co_speakers=["A, X", "B, Y"], co_speaker_genders=["man", "man"])
    config.set_store_config(s, "speaker_gender", "man")
    result = preflight.run(s, pid, today=TODAY)
    finding = findings_by_rule(result)["all-men-panel"]
    assert finding["severity"] == "disqualify" and result["ok"] is False
    assert finding["source"] == LF_URL

    path = store.proposal_path(s, pid)
    meta, body = store.load(path)
    meta["co_speaker_genders"] = ["man"]  # one unknown
    store.save(path, meta, body)
    result = preflight.run(s, pid, today=TODAY)
    finding = findings_by_rule(result)["all-men-panel"]
    assert finding["severity"] == "warn" and "confirm" in finding["text"].lower() and result["ok"] is True

    meta["co_speaker_genders"] = ["man", "woman"]
    store.save(path, meta, body)
    assert "all-men-panel" not in findings_by_rule(preflight.run(s, pid, today=TODAY))

    # "unknown" (what the draft skill allows) counts as unknown, not as not-a-man
    meta["co_speaker_genders"] = ["unknown", "Unknown"]
    store.save(path, meta, body)
    finding = findings_by_rule(preflight.run(s, pid, today=TODAY))["all-men-panel"]
    assert finding["severity"] == "warn" and "2 of 3" in finding["text"]
    # "male" is read as man
    meta["co_speaker_genders"] = ["Male", "M"]
    store.save(path, meta, body)
    assert findings_by_rule(preflight.run(s, pid, today=TODAY))["all-men-panel"]["severity"] == "disqualify"

    duo = make(s, "duo", co_speakers=["A, X"], co_speaker_genders=["man"])
    assert "all-men-panel" not in findings_by_rule(preflight.run(s, duo, today=TODAY))


def test_multi_company_panel(seeded_store):
    s = seeded_store
    pid = make(s, "p", session_type="panel", co_speakers=["A, Example Corp", "B, example corp"], co_speaker_genders=["woman", "woman"])
    result = preflight.run(s, pid, today=TODAY)
    finding = findings_by_rule(result)["multi-company-panel"]
    assert finding["severity"] == "disqualify" and "Example Corp" in finding["text"]
    assert finding["source"] == LF_URL

    path = store.proposal_path(s, pid)
    meta, body = store.load(path)
    meta["co_speakers"] = ["A, Example Corp", "B, Other Inc"]
    store.save(path, meta, body)
    assert "multi-company-panel" not in findings_by_rule(preflight.run(s, pid, today=TODAY))

    meta["co_speakers"] = ["A", "B, Example Corp"]
    store.save(path, meta, body)
    finding = findings_by_rule(preflight.run(s, pid, today=TODAY))["multi-company-panel"]
    assert finding["severity"] == "warn"

    session = make(s, "sess", co_speakers=["A, Example Corp"])
    assert "multi-company-panel" not in findings_by_rule(preflight.run(s, session, today=TODAY))


def test_add_finding_appends_and_recomputes_ok(seeded_store):
    s = seeded_store
    pid = make(s)
    preflight.run(s, pid, today=TODAY)
    result = preflight.add_finding(s, pid, "audience-level", "warn", "Abstract uses advanced terms but level is Beginner.", today=TODAY)
    assert result["ok"] is True and result["findings"][-1]["rule"] == "audience-level"
    assert result["findings"][-1]["source"] == "FR-029 audience level comparison"
    stored = proposals.show(s, pid)["preflight"]
    assert len(stored["findings"]) == 1
    result = preflight.add_finding(s, pid, "custom-check", "disqualify", "Manual block.", source="https://x", today=TODAY)
    assert result["ok"] is False and len(result["findings"]) == 2


CUSTOM_RULE = {
    "id": "roadmap-only", "kind": "custom", "severity": "disqualify", "params": {"session_type": "roadmap"},
    "source": "https://c", "text": "Roadmaps are for staff only.",
}


def add_rule(s, rule):
    path = store.profile_path(s, "kubecon")
    meta, body = frontmatter.load(path)
    meta["rules"].append(dict(rule))
    frontmatter.save(path, meta, body)


def test_manual_rules_carry_severity_and_params(seeded_store):
    s = seeded_store
    add_rule(s, CUSTOM_RULE)
    add_rule(s, {"id": "bare", "kind": "custom", "text": "No severity or params written."})
    pid = make(s)
    manual = {m["rule"]: m for m in preflight.run(s, pid, today=TODAY)["manual"]}
    assert manual["roadmap-only"] == {
        "rule": "roadmap-only", "kind": "custom", "severity": "disqualify", "params": {"session_type": "roadmap"},
        "text": "Roadmaps are for staff only.", "source": "https://c",
    }
    assert manual["vendor-pitch"]["severity"] == "disqualify" and manual["vendor-pitch"]["params"] == {}
    # a rule without a severity counts as disqualify, as profile validate assumes
    assert manual["bare"]["severity"] == "disqualify" and manual["bare"]["params"] == {} and manual["bare"]["source"] == ""


def test_add_finding_for_a_profile_rule_takes_kind_severity_and_source_from_the_profile(seeded_store):
    s = seeded_store
    add_rule(s, CUSTOM_RULE)
    pid = make(s)
    assert preflight.run(s, pid, today=TODAY)["ok"] is True
    result = preflight.add_finding(s, pid, "roadmap-only", None, "The speaker company is not the organizer.", today=TODAY)
    assert result["findings"][-1] == {
        "rule": "roadmap-only", "kind": "custom", "severity": "disqualify",
        "text": "The speaker company is not the organizer.", "source": "https://c",
    }
    assert result["ok"] is False
    # a violated custom disqualify rule blocks ready like any computed rule
    assert any("disqualifying" in reason for reason in lifecycle.ready_check(s, pid)["reasons"])

    # an explicit severity and source win over the profile's (a rule that could not be confirmed)
    preflight.run(s, pid, today=TODAY)
    result = preflight.add_finding(s, pid, "roadmap-only", "warn", "Could not confirm the speaker company.", source="https://other", today=TODAY)
    assert result["findings"][-1]["severity"] == "warn" and result["findings"][-1]["source"] == "https://other"
    assert result["findings"][-1]["kind"] == "custom" and result["ok"] is True


def test_add_finding_needs_a_severity_for_rules_outside_the_profile(seeded_store):
    pid = make(seeded_store)
    preflight.run(seeded_store, pid, today=TODAY)
    with pytest.raises(CfpError, match="severity"):
        preflight.add_finding(seeded_store, pid, "made-up", None, "Text.", today=TODAY)
    with pytest.raises(CfpError, match="severity"):
        preflight.add_finding(seeded_store, pid, "made-up", "fatal", "Text.", today=TODAY)
    assert proposals.show(seeded_store, pid)["preflight"]["findings"] == []


def test_add_finding_cli_uses_profile_rule_defaults(seeded_store, run_cli, write_json):
    add_rule(seeded_store, CUSTOM_RULE)
    add_rule(seeded_store, {"id": "style", "kind": "custom", "severity": "warn", "params": {}, "source": "https://s", "text": "Third person."})
    pid = make(seeded_store, "cli2")
    listed = run_cli("preflight", "--proposal", pid)
    assert {m["rule"]: m["severity"] for m in listed["manual"]} == {"vendor-pitch": "disqualify", "roadmap-only": "disqualify", "style": "warn"}
    added = run_cli("preflight", "add-finding", "--proposal", pid, "--from-json", write_json({"rule": "style", "text": "The abstract says we."}))
    assert added["findings"][-1] == {"rule": "style", "kind": "custom", "severity": "warn", "text": "The abstract says we.", "source": "https://s"}
    assert added["passed"] is True
    added = run_cli("preflight", "add-finding", "--proposal", pid, "--from-json", write_json({"rule": "roadmap-only", "text": "Not staff."}))
    assert added["findings"][-1]["severity"] == "disqualify" and added["passed"] is False
    no_severity = run_cli("preflight", "add-finding", "--proposal", pid, "--from-json", write_json({"rule": "made-up", "text": "t"}), expect_ok=False)
    assert no_severity.code == 1 and "severity" in no_severity["error"]


def test_rules_from_profile_with_params_and_custom_kinds(seeded_store):
    s = seeded_store
    path = store.profile_path(s, "kubecon")
    meta, body = frontmatter.load(path)
    meta["rules"].append({"id": "my-custom", "kind": "custom", "severity": "warn", "params": {}, "source": "https://c", "text": "Check this by hand."})
    for rule in meta["rules"]:
        if rule["kind"] == "submission_limit":
            rule["params"] = {"max": 1}
    frontmatter.save(path, meta, body)
    # the family rule's params.max applies when the event override sets no limit of its own
    event_path = store.event_path(s, "kubecon", EVENT)
    event_meta, event_body = frontmatter.load(event_path)
    event_meta["submission_limit"] = None
    frontmatter.save(event_path, event_meta, event_body)
    make(s, "s0", status="submitted")
    pid = make(s, "second")
    result = preflight.run(s, pid, today=TODAY)
    assert "submission-limit" in findings_by_rule(result)
    assert [m["rule"] for m in result["manual"]] == ["vendor-pitch", "my-custom"]


def test_preflight_cli(seeded_store, run_cli, write_json):
    pid = make(seeded_store, "cli", co_speakers=["A, X", "B, Y"])
    bare = run_cli("preflight", expect_ok=False)
    assert bare.code == 2 and "--proposal" in bare["error"]
    result = run_cli("preflight", "--proposal", pid)
    assert result["ok"] is True and result["passed"] is False and result["findings"][0]["rule"] == "speaker-count"
    assert proposals.show(seeded_store, pid)["preflight"]["ok"] is False
    added = run_cli("preflight", "add-finding", "--proposal", pid, "--rule", "audience-level", "--severity", "warn", "--text", "Mismatch.")
    assert added["findings"][-1]["rule"] == "audience-level" and added["passed"] is False
    bad = run_cli("preflight", "add-finding", "--proposal", pid, "--rule", "x", "--severity", "fatal", "--text", "t", expect_ok=False)
    assert bad.code == 2
    # free text goes through a JSON file, never through shell arguments
    from_file = write_json({"rule": "audience-level", "severity": "warn", "text": "Uses $(dangerous) `text` safely."})
    added = run_cli("preflight", "add-finding", "--proposal", pid, "--from-json", from_file)
    assert added["findings"][-1]["text"] == "Uses $(dangerous) `text` safely."
    missing = run_cli("preflight", "add-finding", "--proposal", pid, "--from-json", write_json({"rule": "r"}), expect_ok=False)
    assert missing.code == 2 and "--text" in missing["error"]
    unknown = run_cli("preflight", "add-finding", "--proposal", pid, "--from-json", write_json({"rule": "r", "severity": "warn", "text": "t", "bogus": 1}), expect_ok=False)
    assert unknown.code == 1 and "bogus" in unknown["error"]
