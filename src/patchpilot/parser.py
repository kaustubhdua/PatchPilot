"""Conservative parser for Git unified-diff text.

The parser counts only lines inside syntactically recognized hunks. It never
executes or interprets submitted source code.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_HEADER = re.compile(r"^diff --git a/(.+) b/(.+)$")
_QUOTED_HEADER = re.compile(r'^diff --git "((?:[^"\\]|\\.)*)" "((?:[^"\\]|\\.)*)"$')
_QUOTED_PREFIX_HEADER = re.compile(
    r'^diff --git (a/"(?:[^"\\]|\\.)*") (b/"(?:[^"\\]|\\.)*")$'
