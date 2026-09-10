from pathlib import Path

import pytest

from namishu_calendar.config import load_config


@pytest.mark.parametrize(
    "config,message",
    [
        ("[", "Invalid YAML"),
        ("- item", "root must be a mapping"),
        ("weekdays:\n  week_start: invalid", "weekdays.week_start"),
        ("weekdays:\n  names: [Monday]", "weekdays.names"),
        ("title:\n  months: [1]", "title.months"),
        ("day_numbers:\n  position: []", "day_numbers.position"),
        ("day_numbers:\n  color: []", "day_numbers.color"),
        ("page:\n  width: .nan", "page.width"),
        ("page:\n  margin_left: 500", "margins"),
        ("font: null", "Invalid font"),
        ("font: {}", "Invalid font"),
        ('font: ""', "Invalid font"),
        ("weekdays:\n  firstday: 6", "Unknown configuration setting"),
    ],
)
def test_invalid_config(tmp_path: Path, config: str, message: str) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(config, encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        load_config(path)


@pytest.mark.parametrize(
    "config,message",
    [
        ("unknown: {}", "Unknown configuration section"),
        ("page: []", "expected mapping"),
        ("page:\n  margin_bottom: 210", "vertical margins"),
        ("page:\n  width: 0", "page.width"),
        ("page:\n  height: -1", "page.height"),
        ("title:\n  font_size: true", "title.font_size"),
        ("grid:\n  gap: -1", "grid.gap"),
        ("grid:\n  gap: .inf", "grid.gap"),
        ("grid:\n  empty_opacity: .nan", "grid.empty_opacity"),
        ("weekdays:\n  names: [Mon, Tue, Wed, Thu, Fri, Sat, '']", "weekdays.names"),
    ],
)
def test_config_boundaries(tmp_path: Path, config: str, message: str) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(config, encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        load_config(path)


@pytest.mark.parametrize("content", ["", "# Only a comment\n", "{}"])
def test_empty_config_uses_defaults(tmp_path: Path, content: str) -> None:
    path = tmp_path / "empty.yaml"
    path.write_text(content, encoding="utf-8")
    assert load_config(path) == load_config()


def test_config_snapshot_and_defaults_are_independent(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("weekdays:\n  week_start: sunday", encoding="utf-8")
    original = load_config(path)
    path.write_text("weekdays:\n  week_start: tuesday", encoding="utf-8")
    assert original["weekdays"]["week_start"] == "sunday"
    assert load_config(path)["weekdays"]["week_start"] == "tuesday"
    original["title"]["months"][0] = "Changed"
    assert load_config()["title"]["months"][0] == "JANUARY"


def test_invalid_utf8(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_bytes(b"\xff")
    with pytest.raises(ValueError, match="Invalid YAML"):
        load_config(path)
