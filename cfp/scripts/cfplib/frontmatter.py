"""Minimal YAML front matter reader and writer (standard library only).

Supported subset (research.md R3): scalars (string, int, float, bool, ISO
date kept as string, null), flat lists, lists of maps, nested maps to any
depth, ``|`` and ``>`` block scalars (folded scalars keep one newline per
blank line), inline ``[]`` and ``{}`` and simple inline lists. Comments on
their own line are skipped and not preserved on rewrite. An inline comment
(whitespace followed by ``#``) after a plain scalar is stripped; ``#``
without preceding whitespace, as inside URLs, survives; after an inline list
the comment must follow the closing bracket. The dumper refuses keys the
parser would not read back and section text that contains a ``## `` line.
Files are written atomically (temporary file plus rename).
"""

import json
import re
from collections import OrderedDict
from pathlib import Path

from cfplib import CfpError, fsutil

DELIM = "---"
_INT_RE = re.compile(r"^-?\d+$")
_FLOAT_RE = re.compile(r"^-?\d+\.\d+$")
_INLINE_COMMENT_RE = re.compile(r"\s+#")
_KEY_RE = re.compile(r"^([A-Za-z0-9_][A-Za-z0-9_ .-]*?)\s*:(\s+|$)")
# Keys the dumper accepts: exactly what the parser reads back as the same key.
_DUMP_KEY_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_ .-]*$")
_HEADING_RE = re.compile(r"^## (.+?)\s*$")


class FrontmatterError(CfpError):
    """Raised when front matter is missing, does not parse, or cannot be written."""

    def __init__(self, path, line, message):
        self.path = str(path) if path else ""
        self.line = line
        self.message = message
        if self.path and line is not None:
            location = f"{self.path}:{line}"
        elif self.path:
            location = self.path
        elif line is not None:
            location = f"line {line}"
        else:
            location = ""
        super().__init__(f"{location}: {message}" if location else message)


# ---------------------------------------------------------------- parsing


class _Line:
    __slots__ = ("number", "indent", "content", "raw")

    def __init__(self, number, raw):
        self.number = number
        self.raw = raw
        stripped = raw.lstrip(" ")
        self.indent = len(raw) - len(stripped)
        self.content = stripped.rstrip()


def _is_structural(line):
    return line.content != "" and not line.content.startswith("#")


def _flow_end(text):
    """Index of the bracket that closes the inline list or map starting `text`, or -1."""
    depth = 0
    quote = None
    skip = False
    for pos, char in enumerate(text):
        if skip:
            skip = False
        elif quote:
            if char == "\\" and quote == '"':
                skip = True
            elif char == quote:
                quote = None
        elif char in "\"'":
            quote = char
        elif char in "[{":
            depth += 1
        elif char in "]}":
            depth -= 1
            if depth == 0:
                return pos
    return -1


def _strip_comment(text):
    """Drop a YAML comment from a plain (unquoted) scalar: '#' at the start or after whitespace.

    For an inline list or map the comment can only follow the closing bracket;
    the text inside the brackets is kept as written.
    """
    if text.startswith("#"):
        return ""
    if text.startswith(('"', "'")):
        return text
    if text.startswith(("[", "{")):
        end = _flow_end(text)
        if end == -1:
            return text
        return text[: end + 1] + _INLINE_COMMENT_RE.split(text[end + 1 :], 1)[0].rstrip()
    return _INLINE_COMMENT_RE.split(text, 1)[0].rstrip()


def _fold(text):
    """Apply YAML folding: line breaks inside a paragraph become spaces, each blank line one newline."""
    folded = ""
    for part in text.split("\n"):
        if part == "":
            folded += "\n"
        elif folded and not folded.endswith("\n"):
            folded += " " + part
        else:
            folded += part
    return folded


class _Parser:
    def __init__(self, lines, path, offset):
        self.lines = lines
        self.path = path
        self.offset = offset

    def error(self, line, message):
        number = line.number if line is not None else self.offset
        raise FrontmatterError(self.path, number, message)

    def next_structural(self, i):
        while i < len(self.lines) and not _is_structural(self.lines[i]):
            i += 1
        return i

    def parse_block(self, i, indent):
        i = self.next_structural(i)
        if i >= len(self.lines):
            return None, i
        line = self.lines[i]
        if line.indent != indent:
            self.error(line, "unexpected indentation")
        if line.content == "-" or line.content.startswith("- "):
            return self.parse_list(i, indent)
        return self.parse_map(i, indent)

    def parse_map(self, i, indent):
        result = OrderedDict()
        while True:
            i = self.next_structural(i)
            if i >= len(self.lines):
                break
            line = self.lines[i]
            if line.indent < indent:
                break
            if line.indent > indent:
                self.error(line, "unexpected indentation")
            if line.content == "-" or line.content.startswith("- "):
                self.error(line, "list item where a key was expected")
            match = _KEY_RE.match(line.content)
            if not match:
                self.error(line, "expected 'key: value'")
            key = match.group(1).strip()
            rest = _strip_comment(line.content[match.end():].strip())
            if key in result:
                self.error(line, f"duplicate key '{key}'")
            if rest == "":
                value, i = self.parse_nested(i + 1, indent)
            elif rest in ("|", "|-", "|+", ">", ">-"):
                value, i = self.parse_block_scalar(i + 1, indent, rest)
            else:
                value = self.parse_scalar(rest, line)
                i += 1
            result[key] = value
        return result, i

    def parse_nested(self, i, parent_indent):
        j = self.next_structural(i)
        if j >= len(self.lines):
            return None, j
        nxt = self.lines[j]
        if nxt.indent > parent_indent:
            return self.parse_block(j, nxt.indent)
        if nxt.indent == parent_indent and (nxt.content == "-" or nxt.content.startswith("- ")):
            return self.parse_list(j, parent_indent)
        return None, j

    def parse_block_scalar(self, i, parent_indent, marker):
        collected = []
        block_indent = None
        while i < len(self.lines):
            line = self.lines[i]
            if line.content == "" and line.raw.strip() == "":
                collected.append("")
                i += 1
                continue
            if line.indent <= parent_indent:
                break
            if block_indent is None:
                block_indent = line.indent
            if line.indent < block_indent:
                self.error(line, "block scalar line indented less than its first line")
            collected.append(line.raw[block_indent:].rstrip("\n"))
            i += 1
        while collected and collected[-1] == "":
            collected.pop()
        text = "\n".join(collected)
        if marker.startswith(">"):
            # Folded scalars keep their paragraph breaks; the writer only emits '|'.
            text = _fold(text)
        if marker.endswith("-"):
            return text, i
        return text + "\n" if text else "", i

    def parse_list(self, i, indent):
        items = []
        while True:
            i = self.next_structural(i)
            if i >= len(self.lines):
                break
            line = self.lines[i]
            if line.indent < indent:
                break
            if line.indent > indent:
                self.error(line, "unexpected indentation")
            if not (line.content == "-" or line.content.startswith("- ")):
                break
            raw_rest = line.content[1:].strip()
            rest = _strip_comment(raw_rest)
            if rest == "":
                # A bare "-" holds a nested value only when the next line is indented
                # deeper; a sibling "-" at the same column means this item is null.
                j = self.next_structural(i + 1)
                if j < len(self.lines) and self.lines[j].indent > indent:
                    value, i = self.parse_block(j, self.lines[j].indent)
                else:
                    value, i = None, i + 1
                items.append(value)
                continue
            if rest in ("|", "|-", ">", ">-"):
                value, i = self.parse_block_scalar(i + 1, indent, rest)
                items.append(value)
                continue
            if _KEY_RE.match(rest):
                # "- key: value" starts a map whose keys sit at the column of `raw_rest`
                inner_indent = indent + (len(line.content) - len(raw_rest))
                self.lines[i] = _Line(line.number, " " * inner_indent + raw_rest)
                value, i = self.parse_map(i, inner_indent)
                items.append(value)
                continue
            items.append(self.parse_scalar(rest, line))
            i += 1
        return items, i

    def parse_scalar(self, text, line):
        text = _strip_comment(text)
        if text == "":
            return None
        if text.startswith('"'):
            try:
                return json.loads(text)
            except ValueError:
                self.error(line, "unterminated or invalid double-quoted string")
        if text.startswith("'"):
            if len(text) < 2 or not text.endswith("'"):
                self.error(line, "unterminated single-quoted string")
            return text[1:-1].replace("''", "'")
        if text == "[]":
            return []
        if text == "{}":
            return {}
        if text.startswith("[") and text.endswith("]"):
            try:
                parsed = json.loads(text)
            except ValueError:
                parsed = None
            if isinstance(parsed, list):
                return parsed
            inner = text[1:-1].strip()
            if not inner:
                return []
            parts = [part.strip() for part in inner.split(",")]
            for part in parts:
                if not part.startswith(('"', "'")) and _INLINE_COMMENT_RE.search(part):
                    self.error(
                        line,
                        "a '#' comment inside an inline list is not supported; "
                        "put the item in double quotes or move the comment after the closing bracket",
                    )
            return [self.parse_scalar(part, line) for part in parts]
        lowered = text.lower()
        if lowered in ("true", "yes"):
            return True
        if lowered in ("false", "no"):
            return False
        if lowered in ("null", "~"):
            return None
        if _INT_RE.match(text):
            return int(text)
        if _FLOAT_RE.match(text):
            return float(text)
        return text


def parse(text, path=None):
    """Split a markdown document into (meta, body).

    Raises FrontmatterError (with path and line) when the delimiters are
    missing or the YAML subset is violated.
    """
    if not text.startswith(DELIM + "\n") and text.strip() != DELIM:
        raise FrontmatterError(path, 1, "file does not start with '---' front matter")
    raw_lines = text.split("\n")
    end = None
    for index in range(1, len(raw_lines)):
        if raw_lines[index].rstrip() == DELIM:
            end = index
            break
    if end is None:
        raise FrontmatterError(path, 1, "missing closing '---' for front matter")
    lines = [_Line(number + 2, raw) for number, raw in enumerate(raw_lines[1:end])]
    parser = _Parser(lines, path, 1)
    first = parser.next_structural(0)
    if first >= len(lines):
        meta = OrderedDict()
    else:
        if lines[first].indent != 0:
            parser.error(lines[first], "unexpected indentation")
        meta, i = parser.parse_map(first, 0)
        i = parser.next_structural(i)
        if i < len(lines):
            parser.error(lines[i], "unexpected content after front matter map")
    body = "\n".join(raw_lines[end + 1:])
    if body.startswith("\n"):
        body = body[1:]
    return dict(meta), body


# ---------------------------------------------------------------- dumping

_NEEDS_QUOTE_START = tuple("-[]{}\"'#*&!%@`|>?,")


def _quote(value):
    return json.dumps(value, ensure_ascii=False)


def _format_scalar(value):
    if value is None:
        return ""
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (int, float)):
        return repr(value) if isinstance(value, float) else str(value)
    text = str(value)
    if text == "":
        return '""'
    if "\n" in text:
        return None  # caller renders a block scalar
    lowered = text.lower()
    if (
        text.startswith(_NEEDS_QUOTE_START)
        or text != text.strip()
        or ": " in text
        or _INLINE_COMMENT_RE.search(text)
        or text.endswith(":")
        or lowered in ("true", "false", "yes", "no", "null", "~")
        or _INT_RE.match(text)
        or _FLOAT_RE.match(text)
    ):
        return _quote(text)
    return text


def _dump_value(out, key_prefix, value, indent):
    """Emit `key_prefix` (like 'key:' or '-') followed by the value."""
    pad = " " * indent
    if isinstance(value, dict):
        if not value:
            out.append(f"{pad}{key_prefix} {{}}")
            return
        out.append(f"{pad}{key_prefix}")
        _dump_map(out, value, indent + 2)
    elif isinstance(value, (list, tuple)):
        if not value:
            out.append(f"{pad}{key_prefix} []")
            return
        out.append(f"{pad}{key_prefix}")
        _dump_list(out, value, indent + 2)
    else:
        scalar = _format_scalar(value)
        if scalar is None:
            marker = "|" if str(value).endswith("\n") else "|-"
            out.append(f"{pad}{key_prefix} {marker}")
            for line in str(value).rstrip("\n").split("\n"):
                out.append(f"{pad}  {line}" if line else "")
        elif scalar == "":
            out.append(f"{pad}{key_prefix}")
        else:
            out.append(f"{pad}{key_prefix} {scalar}")


def _check_key(key):
    """Refuse keys the parser would not read back unchanged (newlines, colons, leading '-')."""
    key = str(key)
    if not _DUMP_KEY_RE.match(key) or key != key.strip():
        raise FrontmatterError(
            None, None, f"invalid front matter key {key!r}: use letters, digits, '_', '-', '.', and single spaces"
        )
    return key


def _dump_map(out, mapping, indent):
    for key, value in mapping.items():
        _dump_value(out, f"{_check_key(key)}:", value, indent)


def _dump_list(out, items, indent):
    pad = " " * indent
    for item in items:
        if isinstance(item, dict):
            if not item:
                out.append(f"{pad}- {{}}")
                continue
            first = True
            for key, value in item.items():
                key = _check_key(key)
                if first:
                    sub = []
                    _dump_value(sub, f"{key}:", value, indent + 2)
                    sub[0] = f"{pad}- " + sub[0][indent + 2:]
                    out.extend(sub)
                    first = False
                else:
                    _dump_value(out, f"{key}:", value, indent + 2)
        elif item is None:
            out.append(f"{pad}- null")  # a bare "-" would read as an empty nested value
        else:
            _dump_value(out, "-", item, indent)


def dump(meta, body):
    """Render meta and body as a markdown document with front matter."""
    out = [DELIM]
    _dump_map(out, meta, 0)
    out.append(DELIM)
    text = "\n".join(out) + "\n"
    body = body or ""
    if body.strip():
        text += "\n" + body.rstrip("\n") + "\n"
    return text


# ---------------------------------------------------------------- body sections


def sections(body):
    """Return an ordered dict of '## Heading' to stripped section text."""
    result = OrderedDict()
    current = None
    buffer = []
    for line in (body or "").split("\n"):
        match = _HEADING_RE.match(line)
        if match:
            if current is not None:
                result[current] = "\n".join(buffer).strip()
            current = match.group(1)
            buffer = []
        elif current is not None:
            buffer.append(line)
    if current is not None:
        result[current] = "\n".join(buffer).strip()
    return result


def preamble(body):
    """Text before the first '## ' heading."""
    lines = []
    for line in (body or "").split("\n"):
        if _HEADING_RE.match(line):
            break
        lines.append(line)
    return "\n".join(lines).strip()


def _check_section_text(text, where):
    """A line starting with '## ' inside section text would split the section on reload."""
    for line in (text or "").split("\n"):
        if _HEADING_RE.match(line):
            raise FrontmatterError(
                None,
                None,
                f"{where} contains a line starting with '## ' ({line.strip()!r}); "
                "use a deeper heading level or plain text inside a section",
            )


def build_body(pre, section_map):
    """Assemble a body from preamble text and an ordered heading to text map.

    Raises FrontmatterError when a section text contains a '## ' line, since
    that line would become a new section when the file is read back.
    """
    parts = []
    if pre and pre.strip():
        _check_section_text(pre, "the preamble")
        parts.append(pre.strip() + "\n")
    for heading, text in section_map.items():
        _check_section_text(text, f"section '{heading}'")
        chunk = f"## {heading}\n"
        if text and text.strip():
            chunk += "\n" + text.strip() + "\n"
        parts.append(chunk)
    return "\n".join(parts)


def set_section(body, heading, text):
    """Replace the text of a section or append it at the end."""
    current = sections(body)
    current[heading] = text or ""
    return build_body(preamble(body), current)


def get_section(body, heading, default=""):
    return sections(body).get(heading, default)


# ---------------------------------------------------------------- files


def load(path):
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        raise CfpError(f"file not found: {path}")
    except UnicodeDecodeError as error:
        raise FrontmatterError(path, 1, f"file is not valid UTF-8: {error.reason}")
    except OSError as error:
        raise FrontmatterError(path, 1, f"cannot read file: {error.strerror or error}")
    return parse(text, path=path)


def save(path, meta, body):
    """Write a front matter file atomically; see ``fsutil.write_text_atomic``."""
    return fsutil.write_text_atomic(path, dump(meta, body))
