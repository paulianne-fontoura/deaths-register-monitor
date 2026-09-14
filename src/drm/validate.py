"""Light structural checks on a downloaded file."""

from pathlib import Path

from drm.config import RECORD_LENGTH


def check_fixed_width(path: Path, record_length: int = RECORD_LENGTH) -> dict:
    """Count lines and lines too short for the record layout.

    The official layout is 176 characters, and INSEE documents that records
    may carry trailing non-significant characters, so longer lines are normal.
    A line is unusable only when it is too short to cut every field. Bad lines
    are counted here and quarantined at parsing time, never fixed silently.
    """
    lines = 0
    bad_lines = 0
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            lines += 1
            if len(line.rstrip("\r\n")) < record_length:
                bad_lines += 1
    return {"lines": lines, "bad_lines": bad_lines}
