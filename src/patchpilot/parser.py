"""Conservative parser for Git unified-diff text.

The parser counts only lines inside syntactically recognized hunks. It never
executes or interprets submitted source code.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_HEADER = re.compile(r"^diff --git a/(.+) b/(.+)$")
_HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?:.*)$")
_RENAME_TO = "rename to "
_NEW_FILE = "new file mode "
_DELETED_FILE = "deleted file mode "


@dataclass(slots=True)
class ParsedFile:
    """Summary of a single file section in a unified diff."""

    path: str
    old_path: str | None = None
    additions: int = 0
    deletions: int = 0
    added_lines: list[str] = field(default_factory=list)
    added_line_numbers: list[int] = field(default_factory=list)
    binary: bool = False
    renamed: bool = False
    deleted: bool = False
    new_file: bool = False
    malformed_hunks: int = 0


def _unquote_git_path(path: str) -> str:
    """Decode Git's C-style quoted paths, including escaped UTF-8 bytes."""
    prefix = ""
    if path.startswith(('a/"', 'b/"')):
        prefix, path = path[:2], path[2:]
    if len(path) < 2 or path[0] != '"' or path[-1] != '"':
        return prefix + path
    body = path[1:-1]
    result: list[str] = []
    index = 0
    escapes = {
        "a": "\a", "b": "\b", "t": "\t", "n": "\n",
        "v": "\v", "f": "\f", "r": "\r", '"': '"', "\\": "\\",
    }
    while index < len(body):
        char = body[index]
        if char != "\\" or index + 1 >= len(body):
            result.append(char)
            index += 1
            continue
        nxt = body[index + 1]
        if nxt in "01234567":
            octets = bytearray()
            while index + 1 < len(body) and body[index] == "\\" and body[index + 1] in "01234567":
                end = index + 1
                while end < min(index + 4, len(body)) and body[end] in "01234567":
                    end += 1
                octets.append(int(body[index + 1 : end], 8))
                index = end
            result.append(octets.decode("utf-8", errors="surrogateescape"))
            continue
        if nxt in escapes:
            result.append(escapes[nxt])
            index += 2
            continue
        result.extend(("\\", nxt))
        index += 2
    return prefix + "".join(result)


def _header_path(value: str, prefix: str) -> str | None:
    value = _unquote_git_path(value.strip())
    if value == "/dev/null":
        return None
    if value.startswith(prefix):
        value = value[len(prefix) :]
    return value


def _diff_header_paths(line: str) -> tuple[str, str] | None:
    """Extract old/new paths from quoted or unquoted Git diff headers."""
    quoted_prefix = _QUOTED_PREFIX_HEADER.match(line)
    if quoted_prefix:
        return (
            _unquote_git_path(quoted_prefix.group(1))[2:],
            _unquote_git_path(quoted_prefix.group(2))[2:],
        )
    quoted = _QUOTED_HEADER.match(line)
    if quoted:
        old_path = _unquote_git_path(f'"{quoted.group(1)}"')
        new_path = _unquote_git_path(f'"{quoted.group(2)}"')
        return old_path.removeprefix("a/"), new_path.removeprefix("b/")
    unquoted = _HEADER.match(line)
    if unquoted:
        return unquoted.group(1), unquoted.group(2)
    return None


def parse_unified_diff(diff: str) -> list[ParsedFile]:
    """Parse file metadata, line counts, and added-line locations.

    Incomplete or malformed hunks are not guessed at. This lightweight parser
    does not validate the full Git diff grammar; callers should treat the
    result as heuristic analysis, not as proof that a patch is valid.
    """
    files: list[ParsedFile] = []
    current: ParsedFile | None = None
    old_remaining = new_remaining = 0
    new_line_number = 0
    in_hunk = False

    for line in diff.splitlines():
        header_paths = _diff_header_paths(line)
        if header_paths:
            if current is not None and in_hunk:
                current.malformed_hunks += 1
            old_path, new_path = header_paths
            current = ParsedFile(path=new_path, old_path=old_path)
            files.append(current)
            in_hunk = False
            continue
        if current is None:
            continue

        if line.startswith(_RENAME_TO):
            current.path = _unquote_git_path(line.removeprefix(_RENAME_TO))
            current.renamed = True
            in_hunk = False
            continue
        if line.startswith("rename from "):
            current.old_path = _unquote_git_path(line.removeprefix("rename from "))
            current.renamed = True
            in_hunk = False
            continue
        if line.startswith(_NEW_FILE):
            current.new_file = True
            in_hunk = False
            continue
        if line.startswith(_DELETED_FILE):
            current.deleted = True
            in_hunk = False
            continue
        if line.startswith("Binary files ") or line == "GIT binary patch":
            current.binary = True
            in_hunk = False
            continue
        if not in_hunk and line.startswith("+++ "):
            path = _header_path(line[4:], "b/")
            if path is not None:
                current.path = path
            in_hunk = False
            continue
        if not in_hunk and line.startswith("--- "):
            path = _header_path(line[4:], "a/")
            if path is not None:
                current.old_path = path
            in_hunk = False
            continue
        if line.startswith("@@"):
            if in_hunk:
                current.malformed_hunks += 1
            match = _HUNK.match(line)
            if not match:
                current.malformed_hunks += 1
                in_hunk = False
                continue
            old_remaining = int(match.group(2) or "1")
            new_remaining = int(match.group(4) or "1")
            new_line_number = int(match.group(3))
            in_hunk = old_remaining > 0 or new_remaining > 0
            continue
        if not in_hunk:
            if line.startswith(("+", "-")):
                current.malformed_hunks += 1
            continue
        if line.startswith("\\"):
            # Git's no-newline marker does not consume a hunk line.
            continue
        if line.startswith("+"):
            if new_remaining <= 0:
                current.malformed_hunks += 1
                in_hunk = False
                continue
            current.additions += 1
            current.added_lines.append(line[1:])
            current.added_line_numbers.append(new_line_number)
            new_line_number += 1
            new_remaining -= 1
        elif line.startswith("-"):
            if old_remaining <= 0:
                current.malformed_hunks += 1
                in_hunk = False
                continue
            current.deletions += 1
            old_remaining -= 1
        elif line.startswith(" "):
            if old_remaining <= 0 or new_remaining <= 0:
                current.malformed_hunks += 1
                in_hunk = False
                continue
            old_remaining -= 1
            new_remaining -= 1
            new_line_number += 1
        else:
            current.malformed_hunks += 1
            in_hunk = False
            continue
        if old_remaining == 0 and new_remaining == 0:
            in_hunk = False

    if current is not None and in_hunk:
        current.malformed_hunks += 1
    return files
