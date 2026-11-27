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


def test_nothing_configured_uses_default_store(tmp_store, tmp_home, run_cli):
    default = tmp_home / ".local" / "share" / "cc-cfp" / "store"
    env = dict(os.environ)
    env.pop("CFP_STORE", None)
    completed = subprocess.run(
        [sys.executable, "-I", str(CLI), "profile", "list"], capture_output=True, text=True, env=env
    )
    data = json.loads(completed.stdout)
    assert completed.returncode == 1 and data["ok"] is False
    assert "store not initialized" in data["error"] and str(default) in data["error"]
    shown = run_cli("config", "show", env={"CFP_STORE": None})
    assert shown["store"] == str(default) and shown["exists"] is False


UNSET = {"CFP_STORE": None}


def test_config_show_reports_locations_with_nothing_configured(tmp_home, run_cli):
    shown = run_cli("config", "show", env=UNSET)
    data_dir = tmp_home / ".local" / "share" / "cc-cfp"
    assert shown["store"] == str(data_dir / "store")
    assert shown["store_source"] == "default"
    assert shown["exists"] is False
    assert shown["config"]["speaker_name"] == ""
    assert shown["config_file"] is None
    assert shown["config_write_path"] == str(tmp_home / ".config" / "cc-cfp" / "config.json")
    assert shown["data_dir"] == str(data_dir)
    assert shown["user_profiles_dir"] == str(data_dir / "profiles")


def test_config_show_reports_sources_and_files(tmp_home, tmp_path, tmp_store, run_cli):
    shown = run_cli("config", "show")
    assert shown["store"] == str(tmp_store.resolve()) and shown["store_source"] == "environment"
    shown = run_cli("config", "show", "--store", tmp_path / "cli")
    assert shown["store"] == str((tmp_path / "cli").resolve()) and shown["store_source"] == "argument"

    legacy = tmp_home / ".config" / "cc-cfp" / "config.json"
    legacy.parent.mkdir(parents=True)
    legacy.write_text(json.dumps({"store": str(tmp_path / "old")}))
    env = {"CFP_STORE": None, "XDG_CONFIG_HOME": str(tmp_path / "cfg"), "XDG_DATA_HOME": str(tmp_path / "data")}
    shown = run_cli("config", "show", env=env)
    assert shown["store"] == str((tmp_path / "old").resolve()) and shown["store_source"] == "config"
    assert shown["config_file"] == str(legacy)
    assert shown["config_write_path"] == str(tmp_path / "cfg" / "cc-cfp" / "config.json")
    assert shown["data_dir"] == str(tmp_path / "data" / "cc-cfp")
    assert shown["user_profiles_dir"] == str(tmp_path / "data" / "cc-cfp" / "profiles")


def test_config_show_and_init_fail_on_relative_data_dir(tmp_store, run_cli):
    for args in (("config", "show"), ("config", "init", "--speaker-name", "A")):
        result = run_cli(*args, env={"CFP_DATA_DIR": "rel"}, expect_ok=False)
        assert result.code == 1 and result["ok"] is False
        assert "CFP_DATA_DIR must be an absolute path" in result["error"]
    assert not tmp_store.exists()


def test_config_init_without_store_creates_default(tmp_home, run_cli):
    data_dir = tmp_home / ".local" / "share" / "cc-cfp"
    result = run_cli("config", "init", "--speaker-name", "A", "--seed-dir", SEED_DIR, env=UNSET)
    assert result["store"] == str(data_dir / "store")
    assert (data_dir / "store" / "config.md").is_file()
    write_path = tmp_home / ".config" / "cc-cfp" / "config.json"
    assert result["config_write_path"] == str(write_path)
    assert result["user_profiles_dir"] == str(data_dir / "profiles")
    assert result["warnings"] == []
    assert json.loads(write_path.read_text())["store"] == str(data_dir / "store")
    assert not (data_dir / "profiles").exists()
    shown = run_cli("config", "show", env=UNSET)
    assert shown["store_source"] == "config" and shown["exists"] is True
    assert shown["config_file"] == str(write_path)


def test_config_init_overwrites_malformed_config(tmp_home, tmp_store, run_cli):
    path = tmp_home / ".config" / "cc-cfp" / "config.json"
    path.parent.mkdir(parents=True)
    path.write_text("{broken")
    run_cli("config", "init", "--store", tmp_store, "--speaker-name", "A")
    assert json.loads(path.read_text()) == {"store": str(tmp_store.resolve())}


def test_config_init_warns_when_cfp_store_overrides(tmp_home, tmp_path, run_cli):
    chosen = tmp_path / "chosen"
    other = tmp_path / "other"
    result = run_cli("config", "init", "--store", chosen, "--speaker-name", "A", env={"CFP_STORE": str(other)})
    assert result["warnings"] == [
        f"CFP_STORE is set to '{other}' and overrides the saved store '{chosen.resolve()}' in later sessions"
    ]
    same = run_cli(
        "config", "init", "--store", tmp_home / "x", "--speaker-name", "A", env={"CFP_STORE": "~/x"}
    )
    assert same["warnings"] == []
    from_env = run_cli("config", "init", "--speaker-name", "A", env={"CFP_STORE": str(other)})
    assert from_env["store"] == str(other.resolve()) and from_env["warnings"] == []


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
    assert {f["id"]: f["limit_status"] for f in shown["fields"] if f.get("limit")} == {"title": "unverified", "abstract": "screenshot"}

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
