"""Tests for the paste view renderer (cfplib.pasteview)."""

import pytest

from cfplib import bios, pasteview, proposals, talks

TODAY = "2026-10-09"
EVENT = "kubecon-eu-2027"


@pytest.fixture
def pid(seeded_store):
    s = seeded_store
    talks.write_talk(s, "t", {"title": "T"}, today=TODAY)
    pid = proposals.create(s, "t", "kubecon", EVENT, "session", today=TODAY)["id"]
    proposals.set_field(s, pid, "abstract", "An abstract with two sentences. Here is the second.", today=TODAY)
    proposals.set_field(s, pid, "title", "x" * 80, today=TODAY)
    proposals.set_field(s, pid, "audience_level", "Intermediate", today=TODAY)
    proposals.set_field(s, pid, "track", "Security", today=TODAY)
    proposals.set_field(s, pid, "case_study", "no", today=TODAY)
    proposals.set_field(s, pid, "cncf_projects", "Kubernetes", today=TODAY)
    bios.write_bio(s, "b", "ai", 500, "Test Speaker bio.", today=TODAY)
    bios.write_resource(s, {"id": "rec", "type": "recording", "title": "Rec", "link": "https://r"})
    proposals.set_meta(s, pid, bio="b", resources=["rec"], today=TODAY)
    return pid


def test_json_format_orders_fields_and_flags(seeded_store, pid):
    data = pasteview.render(seeded_store, pid, "json")
    assert data["proposal"] == pid and data["event"] == EVENT
    ids = [f["id"] for f in data["fields"]]
    assert ids == ["title", "abstract", "benefits", "audience_level", "track", "format", "case_study", "previously_presented", "cncf_projects", "open_source_projects", "resources"]
    by_id = {f["id"]: f for f in data["fields"]}
    assert by_id["title"]["chars"] == 80 and by_id["title"]["limit"] == 75
    assert "OVER LIMIT" in by_id["title"]["flags"] and "limit unverified" in by_id["title"]["flags"]
    assert by_id["abstract"]["flags"] == ["limit unverified"]
    assert by_id["audience_level"]["text"] == "Intermediate" and by_id["audience_level"]["flags"] == []
    assert by_id["track"]["text"] == "Security"
    assert by_id["case_study"]["text"] == "No"
    assert by_id["resources"]["text"] == "Rec: https://r"
    assert by_id["benefits"]["text"] == "" and "not drafted" in by_id["benefits"]["flags"]
    assert by_id["cncf_projects"]["limit"] is None and by_id["cncf_projects"]["status"] == "no-limit"
    assert by_id["cncf_projects"]["flags"] == [] and by_id["cncf_projects"]["limit_status"] is None
    assert by_id["format"]["audience"] == "public" and by_id["benefits"]["audience"] == "reviewer"
    assert data["bio"]["text"] == "Test Speaker bio." and data["bio"]["chars"] == 17 and data["bio"]["limit"] == 500
    assert data["bio"]["flags"] == ["limit unverified"]
    assert data["over"] == ["title"] and "benefits" in data["missing_required"]
    assert any("approximate" in w for w in data["warnings"])


def test_markdown_format(seeded_store, pid):
    text = pasteview.render(seeded_store, pid, "markdown")
    lines = text.split("\n")
    assert lines[0].startswith("# Paste view")
    assert text.index("Session Title") < text.index("Session Description") < text.index("Benefits to the Ecosystem")
    assert "80/75 chars (limit approximate, unverified) [OVER LIMIT, limit unverified]" in text
    assert "10 chars (no limit)" in text
    assert "Intermediate" in text and "Security" in text
    assert text.rstrip().split("\n## ")[-1].startswith("Speaker bio")
    assert "17/500" in text
    assert "not drafted" in text
    assert chr(0x2014) not in text and chr(0x2013) not in text


def test_pasteview_cli_markdown_and_json(seeded_store, pid, run_cli):
    import subprocess
    import sys

    from conftest import CLI

    completed = subprocess.run(
        [sys.executable, "-I", str(CLI), "pasteview", "--proposal", pid, "--format", "markdown"],
        capture_output=True, text=True,
    )
    assert completed.returncode == 0
    assert completed.stdout.startswith("# Paste view")
    result = run_cli("pasteview", "--proposal", pid)
    assert result["proposal"] == pid and result["fields"][0]["id"] == "title"
    result = run_cli("pasteview", "--proposal", pid, "--format", "json")
    assert result["fields"][0]["flags"] == ["OVER LIMIT", "limit unverified"]
    assert result["bio"]["chars"] == 17 and result["over"] == ["title"]
