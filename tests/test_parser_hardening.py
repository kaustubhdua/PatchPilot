from patchpilot.parser import parse_unified_diff


def test_hunk_counts_stop_after_declared_ranges():
    diff = (
        "diff --git a/a.py b/a.py\n"
        "--- a/a.py\n+++ b/a.py\n"
        "@@ -1,1 +1,1 @@\n-old()\n+new()\n+outside_hunk()\n"
    )
    parsed = parse_unified_diff(diff)
    assert parsed[0].additions == 1
    assert parsed[0].deletions == 1
    assert parsed[0].added_lines == ["new()"]


def test_zero_length_hunk_counts_added_file():
    diff = (
        "diff --git a/new.py b/new.py\nnew file mode 100644\n"
        "--- /dev/null\n+++ b/new.py\n@@ -0,0 +1,2 @@\n+one()\n+two()\n"
    )
    parsed = parse_unified_diff(diff)
    assert parsed[0].new_file
    assert parsed[0].additions == 2
    assert parsed[0].deletions == 0


def test_deleted_file_counts_deletions():
    diff = (
        "diff --git a/old.py b/old.py\ndeleted file mode 100644\n"
        "--- a/old.py\n+++ /dev/null\n@@ -1,2 +0,0 @@\n-one()\n-two()\n"
    )
    parsed = parse_unified_diff(diff)
    assert parsed[0].deleted
    assert parsed[0].path == "old.py"
    assert parsed[0].deletions == 2
    assert parsed[0].additions == 0


def test_context_lines_consume_both_ranges():
    diff = (
        "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n"
        "@@ -1,2 +1,2 @@\n before()\n-old()\n+new()\n"
    )
    parsed = parse_unified_diff(diff)
    assert parsed[0].additions == 1
    assert parsed[0].deletions == 1


def test_hunk_with_overrun_is_flagged_and_not_counted_after_range():
    diff = (
        "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n"
        "@@ -0,0 +1,1 @@\n+inside()\n+outside()\n"
    )
    parsed = parse_unified_diff(diff)
    assert parsed[0].additions == 1
    assert parsed[0].malformed_hunks == 1


def test_quoted_git_paths_decode_escaped_tab():
    diff = (
        'diff --git a/"tab\\\\tname.py" b/"tab\\\\tname.py"\n'
        '--- a/"tab\\\\tname.py"\n+++ b/"tab\\\\tname.py"\n'
        "@@ -0,0 +1 @@\n+safe()\n"
    )
    parsed = parse_unified_diff(diff)
    assert len(parsed) == 1
    assert parsed[0].path == "tab\\tname.py"


def test_multiple_hunks_in_same_file():
    diff = (
        "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n"
        "@@ -1 +1 @@\n-a()\n+A()\n"
        "@@ -10 +10 @@\n-b()\n+B()\n"
    )
    parsed = parse_unified_diff(diff)
    assert parsed[0].additions == 2
    assert parsed[0].deletions == 2
