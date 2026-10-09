"""Tests for the stdlib-only YAML front matter subset parser."""

import pytest

from cfplib import frontmatter
from cfplib.frontmatter import FrontmatterError


def test_parse_scalars():
    text = (
        "---\n"
        "name: Short Bio\n"
        "count: 437\n"
        "ratio: 4.5\n"
        "approved: true\n"
        "retired: false\n"
        "created: 2026-10-09\n"
        "---\n"
        "Body text\n"
    )
    meta, body = frontmatter.parse(text)
    assert meta["name"] == "Short Bio"
    assert meta["count"] == 437 and isinstance(meta["count"], int)
    assert meta["ratio"] == 4.5
    assert meta["approved"] is True
    assert meta["retired"] is False
    assert meta["created"] == "2026-10-09"
    assert body == "Body text\n"


def test_parse_unquoted_colons_hash_and_urls():
    text = (
        "---\n"
        "track: Platform Engineering: DevEx & IDPs\n"
        "source: https://events.linuxfoundation.org/kubecon-cloudnativecon-europe/program/cfp/#section\n"
        "note: value with # an inline comment\n"
        'quoted: "value with # inside"\n'
        "limit: 75 # confirmed by email\n"
        "empty: # only a comment\n"
        "tag: C#\n"
        "---\n"
    )
    meta, body = frontmatter.parse(text)
    assert meta["track"] == "Platform Engineering: DevEx & IDPs"
    assert meta["source"] == "https://events.linuxfoundation.org/kubecon-cloudnativecon-europe/program/cfp/#section"
    assert meta["note"] == "value with"  # whitespace then '#' starts a YAML comment
    assert meta["quoted"] == "value with # inside"
    assert meta["limit"] == 75
    assert meta["empty"] is None
    assert meta["tag"] == "C#"
    assert body == ""
    # the dumper quotes values that contain whitespace then '#', so they survive a round trip
    again, _ = frontmatter.parse(frontmatter.dump({"v": "keep # this", "t": "keep\t# this"}, ""))
    assert again["v"] == "keep # this" and again["t"] == "keep\t# this"


def test_comment_after_key_before_nested_block():
    text = "---\nfields: # the fields\n  - id: title # first\n    kind: text\nm: # note\n  k: v\nl:\n  - # first item\n    id: a\n---\n"
    meta, _ = frontmatter.parse(text)
    assert meta["fields"] == [{"id": "title", "kind": "text"}]
    assert meta["m"] == {"k": "v"}
    assert meta["l"] == [{"id": "a"}]


def test_save_keeps_file_mode(tmp_path):
    import os
    import stat

    path = tmp_path / "private.md"
    frontmatter.save(path, {"a": 1}, "")
    os.chmod(path, 0o600)
    frontmatter.save(path, {"a": 2}, "")
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_save_follows_symlink_to_real_file(tmp_path):
    real = tmp_path / "real.md"
    frontmatter.save(real, {"a": 1}, "")
    link = tmp_path / "link.md"
    link.symlink_to(real)
    frontmatter.save(link, {"a": 2}, "")
    assert link.is_symlink() and frontmatter.load(real)[0] == {"a": 2}


def test_parse_inline_json_list_and_bom():
    text = '﻿---\ntags: ["a, b", "c"]\nplain: [x, 2, true]\n---\n'
    meta, _ = frontmatter.parse(text.lstrip("﻿"))
    assert meta["tags"] == ["a, b", "c"] and meta["plain"] == ["x", 2, True]


def test_load_reports_bom_and_bad_encoding(tmp_path):
    bom = tmp_path / "bom.md"
    bom.write_text("﻿---\nname: x\n---\n", encoding="utf-8")
    assert frontmatter.load(bom)[0] == {"name": "x"}
    latin = tmp_path / "latin.md"
    latin.write_bytes(b"---\nname: caf\xe9\n---\n")
    with pytest.raises(frontmatter.FrontmatterError) as info:
        frontmatter.load(latin)
    assert "UTF-8" in str(info.value) and str(latin) in str(info.value)


def test_save_is_atomic_and_leaves_no_temp_file(tmp_path):
    path = tmp_path / "a.md"
    frontmatter.save(path, {"name": "x"}, "")
    frontmatter.save(path, {"name": "y"}, "body")
    assert [p.name for p in tmp_path.iterdir()] == ["a.md"]
    assert frontmatter.load(path) == ({"name": "y"}, "body\n")


def test_parse_quoted_strings_and_empty_values():
    text = (
        "---\n"
        'seed_version: "2026-10-09"\n'
        "single: 'it''s quoted'\n"
        'escaped: "line: one \\"two\\""\n'
        "submitted_on:\n"
        'empty: ""\n'
        "---\n"
    )
    meta, _ = frontmatter.parse(text)
    assert meta["seed_version"] == "2026-10-09"
    assert meta["single"] == "it's quoted"
    assert meta["escaped"] == 'line: one "two"'
    assert meta["submitted_on"] is None
    assert meta["empty"] == ""
    dumped = frontmatter.dump(meta, "")
    assert "submitted_on:\n" in dumped
    assert 'empty: ""' in dumped
    again, _ = frontmatter.parse(dumped)
    assert again == meta


def test_parse_flat_lists_and_inline_empty():
    text = (
        "---\n"
        "personas:\n"
        "  - Platform engineers\n"
        "  - SREs\n"
        "co_speakers: []\n"
        "preflight: {}\n"
        "tags: [a, b]\n"
        "---\n"
    )
    meta, _ = frontmatter.parse(text)
    assert meta["personas"] == ["Platform engineers", "SREs"]
    assert meta["co_speakers"] == []
    assert meta["preflight"] == {}
    assert meta["tags"] == ["a", "b"]


def test_parse_list_of_maps_and_nested_maps():
    text = (
        "---\n"
        "fields:\n"
        "  - id: title\n"
        "    label: Session Title\n"
        "    required: true\n"
        "    limit: 75\n"
        "    options:\n"
        "      - Any\n"
        "      - Beginner\n"
        "  - id: abstract\n"
        "    limit:\n"
        "rubric:\n"
        "  scale_max: 5\n"
        "  pass_average: 4.0\n"
        "  criteria:\n"
        "    - id: content\n"
        "      name: Content\n"
        "rules:\n"
        "  - id: submission-limit\n"
        "    params:\n"
        "      max: 3\n"
        "---\n"
    )
    meta, _ = frontmatter.parse(text)
    assert meta["fields"][0] == {
        "id": "title",
        "label": "Session Title",
        "required": True,
        "limit": 75,
        "options": ["Any", "Beginner"],
    }
    assert meta["fields"][1] == {"id": "abstract", "limit": None}
    assert meta["rubric"]["scale_max"] == 5
    assert meta["rubric"]["pass_average"] == 4.0
    assert meta["rubric"]["criteria"] == [{"id": "content", "name": "Content"}]
    assert meta["rules"][0]["params"] == {"max": 3}


def test_parse_block_scalar():
    text = (
        "---\n"
        "guidance: |\n"
        "  First line.\n"
        "\n"
        "  Third line after blank.\n"
        "next: 1\n"
        "---\n"
    )
    meta, _ = frontmatter.parse(text)
    assert meta["guidance"] == "First line.\n\nThird line after blank.\n"
    assert meta["next"] == 1


def test_comments_and_blank_lines_are_skipped():
    text = "---\n# a comment\n\nname: x\n\n# another\nvalue: 2\n---\n"
    meta, _ = frontmatter.parse(text)
    assert meta == {"name": "x", "value": 2}


def test_round_trip_preserves_unknown_keys_and_order():
    text = (
        "---\n"
        "id: talk-1\n"
        "custom_key: keep me\n"
        "personas:\n"
        "  - A\n"
        "outings:\n"
        "  - event: KubeCon EU 2025\n"
        "    date: 2025-04-02\n"
        "    kind: presented\n"
        "rubric:\n"
        "  scale_max: 5\n"
        "---\n"
        "\n"
        "## Problem\n"
        "\n"
        "Text.\n"
    )
    meta, body = frontmatter.parse(text)
    dumped = frontmatter.dump(meta, body)
    meta2, body2 = frontmatter.parse(dumped)
    assert meta2 == meta
    assert list(meta2.keys()) == ["id", "custom_key", "personas", "outings", "rubric"]
    assert body2.strip() == body.strip()
    assert dumped.startswith("---\nid: talk-1\ncustom_key: keep me\n")


def test_dump_quotes_when_needed():
    meta = {
        "track": "Platform Engineering: DevEx & IDPs",
        "dash": "- not a list",
        "num_string": "0042",
        "multi": "line one\nline two",
        "hash": "a # b",
        "nothing": None,
        "flag": True,
    }
    dumped = frontmatter.dump(meta, "")
    meta2, _ = frontmatter.parse(dumped)
    assert meta2 == meta


def test_sections_split_by_h2():
    body = (
        "Preamble text.\n\n"
        "## Problem\n\nThe problem.\n\n"
        "## Takeaways\n\n- one\n- two\n\n"
        "## Empty\n\n"
    )
    sections = frontmatter.sections(body)
    assert list(sections.keys()) == ["Problem", "Takeaways", "Empty"]
    assert sections["Problem"] == "The problem."
    assert sections["Takeaways"] == "- one\n- two"
    assert sections["Empty"] == ""


def test_set_section_replaces_and_appends():
    body = "## Problem\n\nOld.\n\n## Takeaways\n\n- one\n"
    body = frontmatter.set_section(body, "Problem", "New problem.")
    assert frontmatter.sections(body)["Problem"] == "New problem."
    assert frontmatter.sections(body)["Takeaways"] == "- one"
    body = frontmatter.set_section(body, "Story notes", "Notes.")
    assert list(frontmatter.sections(body).keys()) == ["Problem", "Takeaways", "Story notes"]
    assert frontmatter.sections(body)["Story notes"] == "Notes."
    body = frontmatter.set_section("", "Bio", "Bio text.")
    assert frontmatter.sections(body) == {"Bio": "Bio text."}


def test_parse_error_reports_path_and_line():
    text = "---\nname: x\n  bad indent: y\n---\n"
    with pytest.raises(FrontmatterError) as info:
        frontmatter.parse(text, path="/store/talks/x.md")
    assert info.value.path == "/store/talks/x.md"
    assert info.value.line == 3
    assert "/store/talks/x.md" in str(info.value)


def test_missing_closing_delimiter_is_an_error():
    with pytest.raises(FrontmatterError) as info:
        frontmatter.parse("---\nname: x\nbody without end\n", path="f.md")
    assert info.value.line == 1


def test_no_front_matter_is_an_error():
    with pytest.raises(FrontmatterError):
        frontmatter.parse("# Just a heading\n", path="f.md")


def test_load_and_save_files(tmp_path):
    path = tmp_path / "x.md"
    frontmatter.save(path, {"id": "x", "n": 1}, "## A\n\nText.\n")
    meta, body = frontmatter.load(path)
    assert meta == {"id": "x", "n": 1}
    assert frontmatter.sections(body)["A"] == "Text."


def test_empty_list_item_is_null_and_does_not_swallow_siblings():
    text = "---\nitems:\n  -\n  - second\n  - third\nnested:\n  -\n    id: a\n  - id: b\n---\n"
    meta, _ = frontmatter.parse(text)
    assert meta["items"] == [None, "second", "third"]
    assert meta["nested"] == [{"id": "a"}, {"id": "b"}]
    # a None item is written as "- null" so it reads back as one item, not as a nested list
    dumped = frontmatter.dump({"items": [None, "x"]}, "")
    assert "- null\n" in dumped
    assert frontmatter.parse(dumped)[0]["items"] == [None, "x"]


def test_folded_scalar_keeps_paragraph_breaks():
    text = "---\nguidance: >\n  First line\n  of one paragraph.\n\n  Second paragraph.\n\n\n  Third.\nnext: 1\n---\n"
    meta, _ = frontmatter.parse(text)
    assert meta["guidance"] == "First line of one paragraph.\nSecond paragraph.\n\nThird.\n"
    assert meta["next"] == 1
    stripped, _ = frontmatter.parse("---\ng: >-\n  a\n  b\n\n  c\n---\n")
    assert stripped["g"] == "a b\nc"
    # the writer emits a literal block, which reads back unchanged
    assert frontmatter.parse(frontmatter.dump(meta, ""))[0] == meta


def test_inline_list_comment_only_after_closing_bracket():
    meta, _ = frontmatter.parse('---\na: [x, z] # trailing\nb: [a, "b # c"] # note\nc: [] # empty\n---\n')
    assert meta["a"] == ["x", "z"]
    assert meta["b"] == ["a", "b # c"]
    assert meta["c"] == []
    with pytest.raises(FrontmatterError) as info:
        frontmatter.parse("---\na: [x # y, z]\n---\n")
    assert info.value.line == 2 and "inline list" in str(info.value)
    # a list item with an inline list behaves the same way
    meta, _ = frontmatter.parse("---\nl:\n  - [1, 2] # pair\n---\n")
    assert meta["l"] == [[1, 2]]


def test_dump_rejects_keys_the_parser_cannot_read_back():
    for key in ("multi\nline", "has: colon", " padded", "", "-dash", "tab\tkey"):
        with pytest.raises(FrontmatterError) as info:
            frontmatter.dump({key: 1}, "")
        assert "invalid front matter key" in str(info.value)
    with pytest.raises(FrontmatterError):
        frontmatter.dump({"fields": [{"ok": 1, "bad\nkey": 2}]}, "")
    with pytest.raises(FrontmatterError):
        frontmatter.dump({"rubric": {"bad: key": 2}}, "")
    # keys the parser accepts (spaces, dots, dashes) still round-trip
    meta = {"my key": 1, "a.b-c": 2, "x_1": 3}
    assert frontmatter.parse(frontmatter.dump(meta, ""))[0] == meta


def test_save_with_invalid_key_leaves_no_file_behind(tmp_path):
    path = tmp_path / "x.md"
    with pytest.raises(FrontmatterError):
        frontmatter.save(path, {"bad\nkey": 1}, "")
    assert list(tmp_path.iterdir()) == []


def test_section_text_with_h2_line_is_rejected():
    with pytest.raises(FrontmatterError) as info:
        frontmatter.set_section("## Problem\n\nP.\n", "Problem", "Intro.\n\n## Sneaky heading\n\nMore.")
    message = str(info.value)
    assert "Problem" in message and "## " in message
    with pytest.raises(FrontmatterError):
        frontmatter.build_body("Preamble\n## Not a preamble", {"A": "a"})
    # deeper headings and hashes without a space are ordinary text
    body = frontmatter.set_section("", "Problem", "### Sub heading\n\n#tag and ##double")
    assert frontmatter.sections(body) == {"Problem": "### Sub heading\n\n#tag and ##double"}


def test_round_trip_non_ascii(tmp_path):
    meta = {"name": "Roland Huß", "note": "Grüße aus München 🎉", "tags": ["Ä", "😀"], "quoted": "ß: colon"}
    body = "## Bio\n\nRoland Huß spricht über Kubernetes 🚀.\n"
    dumped = frontmatter.dump(meta, body)
    assert "Roland Huß" in dumped and "\\u" not in dumped
    meta2, body2 = frontmatter.parse(dumped)
    assert meta2 == meta and body2 == body
    path = tmp_path / "unicode.md"
    frontmatter.save(path, meta, body)
    assert frontmatter.load(path) == (meta, body)
