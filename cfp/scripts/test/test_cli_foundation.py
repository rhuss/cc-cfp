"""Runs each foundation subcommand of cfp_store.py through a subprocess."""

import json
import os
import subprocess
import sys

from conftest import CLI, SEED_DIR, TEMPLATES_DIR


def test_config_init_show_set(tmp_store, run_cli):
    result = run_cli(
        "config", "init", "--store", tmp_store, "--speaker-name", "Test Speaker",
        "--speaker-company", "Example", "--review-rounds", "2", "--seed-dir", SEED_DIR,
    )
    assert result["seeded_profiles"] == ["kubecon"]
    assert result["store"] == str(tmp_store.resolve())
    shown = run_cli("config", "show")
    assert shown["exists"] is True
    assert shown["config"]["speaker_name"] == "Test Speaker"
    assert shown["config"]["review_rounds"] == 2
    assert shown["config"]["default_profile"] == "kubecon"
    changed = run_cli("config", "set", "--key", "voice_profile", "--value", "blog")
    assert changed["key"] == "voice_profile" and changed["value"] == "blog"
    assert run_cli("config", "show")["config"]["voice_profile"] == "blog"
    bad = run_cli("config", "set", "--key", "review_rounds", "--value", "many", expect_ok=False)
    assert bad.code == 1 and "integer" in bad["error"]
    assert run_cli("config", "show")["config"]["review_rounds"] == 2


def test_config_init_keeps_non_ascii_speaker_name(tmp_store, run_cli):
    run_cli("config", "init", "--store", tmp_store, "--speaker-name", "Roland Huß 🎤")
    assert run_cli("config", "show")["config"]["speaker_name"] == "Roland Huß 🎤"
    assert "Roland Huß 🎤" in (tmp_store / "config.md").read_text(encoding="utf-8")


def test_missing_store_is_domain_error(tmp_store, run_cli):
    result = run_cli("profile", "list", expect_ok=False)
    assert result.code == 1
    assert result.data["ok"] is False and "config init" in result.data["error"]


def test_no_store_configured_at_all(tmp_store, run_cli, monkeypatch):
    env = dict(os.environ)
    env.pop("CFP_STORE", None)
    completed = subprocess.run(
        [sys.executable, "-I", str(CLI), "profile", "list"], capture_output=True, text=True, env=env
    )
    data = json.loads(completed.stdout)
    assert completed.returncode == 1 and data["ok"] is False and "store" in data["error"]


def test_usage_error_exits_2(run_cli):
    result = run_cli("profile", "bogus", expect_ok=False)
    assert result.code == 2
    assert result.data["ok"] is False and "usage" in result.data["error"].lower()
    result = run_cli(expect_ok=False)
    assert result.code == 2


def test_profile_subcommands(seeded_store, run_cli, write_json):
    listing = run_cli("profile", "list")
    assert listing["profiles"][0]["id"] == "kubecon"
    assert listing["profiles"][0]["approved"] is True
    assert listing["problems"] == []
    events = {e["id"]: e for e in listing["profiles"][0]["events"]}
    assert events["kubecon-eu-2027"]["days_to_close"] == 2

    shown = run_cli("profile", "show", "--profile", "kubecon", "--event", "kubecon-eu-2027")
    assert len(shown["tracks"]) == 13
    assert next(t for t in shown["session_types"] if t["id"] == "tutorial")["duration_min"] == 80
    assert all(f.get("limit_status", "unverified") == "unverified" for f in shown["fields"] if f.get("limit"))

    valid = run_cli("profile", "validate", "--profile", "kubecon", "--event", "kubecon-eu-2027")
    assert valid["valid"] is True and valid["problems"] == []

    written = run_cli("profile", "write", "--profile", "newconf", "--from-json", write_json({"name": "New Conf", "platform": "pretalx", "body": {"Drafting guidance": "G"}}))
    assert written["path"].endswith("profiles/newconf/profile.md")
    assert run_cli("profile", "show", "--profile", "newconf")["approved"] is False
    approved = run_cli("profile", "approve", "--profile", "newconf")
    assert approved["approved"] is True
    revoked = run_cli("profile", "approve", "--profile", "newconf", "--revoke")
    assert revoked["approved"] is False

    unknown = run_cli("profile", "show", "--profile", "nope", expect_ok=False)
    assert unknown.code == 1 and "unknown profile" in unknown.data["error"]


def test_event_and_example_subcommands(seeded_store, run_cli, write_json):
    written = run_cli("event", "write", "--profile", "kubecon", "--event", "kubecon-india-2026", "--from-json", write_json({"name": "KubeCon India 2026", "tracks": ["AI"], "cfp_close": "2026-02-01"}))
    assert written["path"].endswith("events/kubecon-india-2026.md")
    events = run_cli("event", "list", "--profile", "kubecon")
    by_id = {e["id"]: e for e in events["events"]}
    assert by_id["kubecon-india-2026"]["approved"] is False
    assert by_id["kubecon-india-2026"]["days_to_close"] < 0
    assert events["problems"] == []
    approved = run_cli("profile", "approve", "--profile", "kubecon", "--event", "kubecon-india-2026")
    assert approved["approved"] is True

    added = run_cli("example", "add", "--profile", "kubecon", "--from-json", write_json({"title": "Accepted Talk", "abstract": "A", "benefits": "B", "event": "kubecon-eu-2026", "year": 2026, "origin": "manual"}))
    assert added["path"].endswith("examples/accepted-talk.md")
    examples = run_cli("example", "list", "--profile", "kubecon", "--limit", "1")
    assert examples["examples"][0]["title"] == "Accepted Talk"
    assert len(run_cli("example", "list", "--profile", "kubecon")["examples"]) == 2


def test_bio_and_resource_subcommands(seeded_store, run_cli, write_text, write_json):
    written = run_cli("bio", "write", "--name", "short", "--emphasis", "cloud-native", "--target-length", "450", "--text-file", write_text("Test Speaker builds things.\n"))
    assert written["chars"] == len("Test Speaker builds things.")
    listing = run_cli("bio", "list")
    assert listing["bios"][0]["name"] == "short" and listing["problems"] == []
    shown = run_cli("bio", "show", "--name", "short")
    assert shown["text"] == "Test Speaker builds things."
    assert run_cli("bio", "delete", "--name", "short")["deleted"].endswith("short.md")
    assert run_cli("bio", "list")["bios"] == []

    resource = run_cli("resource", "write", "--from-json", write_json({"type": "recording", "title": "A Recording", "link": "https://youtu.be/x", "date": "2025-04-02"}))
    assert resource["id"] == "a-recording"
    assert run_cli("resource", "list", "--type", "recording")["resources"][0]["id"] == "a-recording"
    assert run_cli("resource", "list", "--type", "blog")["resources"] == []
    assert run_cli("resource", "delete", "--id", "a-recording")["deleted"].endswith("a-recording.md")


def test_status_subcommands(seeded_store, run_cli):
    from cfplib import frontmatter, store

    meta, body = frontmatter.load(TEMPLATES_DIR / "talk.md")
    meta.update({"id": "my-talk", "title": "My Talk"})
    store.save(store.talk_path(seeded_store, "my-talk"), meta, body)
    meta, body = frontmatter.load(TEMPLATES_DIR / "proposal.md")
    meta.update({"id": "kubecon-eu-2027--my-talk", "talk": "my-talk", "profile": "kubecon", "event": "kubecon-eu-2027"})
    store.save(store.proposal_path(seeded_store, "kubecon-eu-2027--my-talk"), meta, body)

    check = run_cli("status", "ready-check", "--proposal", "kubecon-eu-2027--my-talk")
    assert check["can_ready"] is False and len(check["reasons"]) == 2
    forced = run_cli("status", "set", "--proposal", "kubecon-eu-2027--my-talk", "--to", "ready", "--force")
    assert forced["from"] == "draft" and forced["to"] == "ready" and forced["date"] == "2026-10-09"
    moved = run_cli("status", "set", "--proposal", "kubecon-eu-2027--my-talk", "--to", "submitted", "--date", "2026-10-10")
    assert moved["date"] == "2026-10-10"
    bad = run_cli("status", "set", "--proposal", "kubecon-eu-2027--my-talk", "--to", "presented", expect_ok=False)
    assert bad.code == 1 and "allowed targets" in bad.data["error"]
    bad_date = run_cli("status", "set", "--proposal", "kubecon-eu-2027--my-talk", "--to", "accepted", "--date", "soon", expect_ok=False)
    assert bad_date.code == 1 and "ISO" in bad_date["error"]
    assert run_cli("proposal", "show", "--proposal", "kubecon-eu-2027--my-talk")["status"] == "submitted"


def test_list_reports_parse_problems(seeded_store, run_cli):
    (seeded_store / "bios" / "broken.md").write_text("---\nname: broken\n", encoding="utf-8")
    listing = run_cli("bio", "list")
    assert listing["bios"] == []
    assert len(listing["problems"]) == 1 and listing["problems"][0]["path"].endswith("broken.md")


def test_output_is_single_json_object(seeded_store, run_cli):
    result = run_cli("profile", "list")
    assert result.stdout.count("\n") == 1
    json.loads(result.stdout)


def test_example_list_reports_parse_problems(seeded_store, run_cli):
    (seeded_store / "profiles" / "kubecon" / "examples" / "broken.md").write_text("---\nid: broken\n", encoding="utf-8")
    listing = run_cli("example", "list", "--profile", "kubecon")
    assert [e["id"] for e in listing["examples"]] == ["lf-sample-container-runtime"]
    assert len(listing["problems"]) == 1 and listing["problems"][0]["path"].endswith("broken.md")


def test_event_write_resets_approval_unless_json_says_otherwise(seeded_store, run_cli, write_json):
    family_profile = seeded_store / "profiles" / "kubecon" / "profile.md"
    before = family_profile.read_bytes()
    run_cli("event", "write", "--profile", "kubecon", "--event", "kubecon-na-2026", "--from-json", write_json({"tracks": ["X"]}))
    shown = run_cli("profile", "show", "--profile", "kubecon", "--event", "kubecon-na-2026")
    assert shown["approved"] is False and shown["tracks"] == ["X"]
    assert shown["event"]["name"] == "KubeCon + CloudNativeCon North America 2026"
    run_cli("event", "write", "--profile", "kubecon", "--event", "kubecon-na-2026", "--from-json", write_json({"approved": True}))
    assert run_cli("profile", "show", "--profile", "kubecon", "--event", "kubecon-na-2026")["approved"] is True
    # US3 scenario 3: an event override never touches the family profile
    assert family_profile.read_bytes() == before


def test_invalid_today_is_usage_error(seeded_store, run_cli):
    result = run_cli("profile", "list", today="garbage", expect_ok=False)
    assert result.code == 2 and "ISO date" in result.data["error"]
