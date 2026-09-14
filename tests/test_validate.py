from drm.validate import check_fixed_width


def test_short_lines_are_bad_trailing_is_fine(tmp_path):
    sample = tmp_path / "sample.txt"
    lines = ["A" * 176, "B" * 198, "COURT"]
    sample.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert check_fixed_width(sample) == {"lines": 3, "bad_lines": 1}
