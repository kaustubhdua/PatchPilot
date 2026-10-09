"""Unified-diff parsing primitives for PatchPilot."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_HEADER = re.compile(r"^diff --git a/(.+) b/(.+)$")
_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@")
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


def _unquote_git_path(path: str) -> str:
    """Decode Git's quoted path representation conservatively."""
    if len(path) >= 2 and path[0] == '"' and path[-1] == '"':
        body = path[1:-1]
        replacements = {
            r"\\": "\\",
            r'\"': '"',
            r"\t": "\t",
            r"\n": "\n",
        }
        for source, target in replacements.items():
            body = body.replace(source, target)
        return body
    return path


def parse_unified_diff(diff: str) -> list[ParsedFile]:
    """Parse file boundaries and count only lines inside valid hunks.

    This parser deliberately does not try to interpret source code. It supports
    ordinary Git unified diffs, new/deleted files, basic rename metadata and
    binary markers. Malformed or incomplete hunk lines are ignored rather than
    guessed at.
    """
    files: list[ParsedFile] = []
    current: ParsedFile | None = None
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
            path = line[4:]
            if path != "/dev/null":
                current.path = _unquote_git_path(path.removeprefix("b/"))
            in_hunk = False
            continue
        if line.startswith("--- "):
            path = line[4:]
            if path != "/dev/null":
                current.old_path = _unquote_git_path(path.removeprefix("a/"))
            in_hunk = False
            continue
        if line.startswith("@@"):
            in_hunk = bool(_HUNK.match(line))
            continue
        if not in_hunk:
            continue
        if line.startswith("+") and not line.startswith("+++"):
            current.additions += 1
            current.added_lines.append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            current.deletions += 1
        elif line.startswith("\\"):
            # Diff metadata such as "\ No newline at end of file".
            continue
        elif line.startswith(" "):
            continue
        else:
            # Unexpected unprefixed content terminates the current hunk.
            in_hunk = False

    return files
