"""Conservative parser for Git unified-diff text.

The parser counts only lines inside syntactically recognized hunks. It never
executes or interprets submitted source code.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

_HEADER = re.compile(r'^diff --git a/(.+) b/(.+)$')
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
    binary: bool = False
    renamed: bool = False
    deleted: bool = False
    new_file: bool = False
    malformed_hunks: int = 0


def _unquote_git_path(path: str) -> str:
    """Decode common C-style escapes used by Git's quoted path format."""
    if len(path) < 2 or path[0] != '"' or path[-1] != '"':
        return path
    body = path[1:-1]
    result: list[str] = []
    index = 0
    escapes = {"t": "\t", "n": "\n", "r": "\r", '"': '"', "\\": "\\"}
    while index < len(body):
        char = body[index]
        if char != "\\" or index + 1 >= len(body):
            result.append(char)
            index += 1
            continue
        nxt = body[index + 1]
        if nxt in escapes:
            result.append(escapes[nxt])
            index += 2
            continue
        if nxt in "01234567":
            end = index + 1
            while end < min(index + 4, len(body)) and body[end] in "01234567":
                end += 1
            result.append(chr(int(body[index + 1:end], 8)))
            index = end
            continue
        # Preserve unknown escapes instead of silently corrupting the path.
        result.extend(("\\", nxt))
        index += 2
    return "".join(result)


def _header_path(value: str, prefix: str) -> str | None:
    value = value.strip()
    if value == "/dev/null":
        return None
    if value.startswith(prefix):
        value = value[len(prefix):]
    return _unquote_git_path(value)


def parse_unified_diff(diff: str) -> list[ParsedFile]:
    """Parse file metadata and line counts from a unified diff.

    Incomplete or malformed hunks are not guessed at. This lightweight parser
    does not validate the full Git diff grammar; callers should treat the
    result as heuristic analysis, not as proof that a patch is valid.
    """
    files: list[ParsedFile] = []
    current: ParsedFile | None = None
    old_remaining = new_remaining = 0
    in_hunk = False

    for line in diff.splitlines():
        header = _HEADER.match(line)
        if header:
            old_path = _unquote_git_path(header.group(1))
            new_path = _unquote_git_path(header.group(2))
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
        if line.startswith("+++ "):
            path = _header_path(line[4:], "b/")
            if path is not None:
                current.path = path
            in_hunk = False
            continue
        if line.startswith("--- "):
            path = _header_path(line[4:], "a/")
            if path is not None:
                current.old_path = path
            in_hunk = False
            continue
        if line.startswith("@@"):
            match = _HUNK.match(line)
            if not match:
                current.malformed_hunks += 1
                in_hunk = False
                continue
            old_remaining = int(match.group(2) or "1")
            new_remaining = int(match.group(4) or "1")
            in_hunk = True
            # Zero/zero hunks are legal but have no body to consume.
            if old_remaining == 0 and new_remaining == 0:
                in_hunk = False
            continue
        if not in_hunk:
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
        else:
            current.malformed_hunks += 1
            in_hunk = False
            continue
        if old_remaining == 0 and new_remaining == 0:
            in_hunk = False

    return files
