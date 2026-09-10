from __future__ import annotations

from math import isfinite
from pathlib import Path
from typing import Any

import yaml
from reportlab.lib.colors import toColor

DATA_DIR = Path(__file__).resolve().parent / "data"


def _load_yaml(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8") as stream:
            data = yaml.safe_load(stream)
    except (yaml.YAMLError, UnicodeError) as exc:
        raise ValueError(f"Invalid YAML configuration: {path}: {exc}") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")
    return data


def load_config(config_path: str | Path | None = None) -> dict:
    config = _load_yaml(DATA_DIR / "default.yaml")
    config["font"] = str(DATA_DIR / config["font"])
    if config_path is not None:
        path = Path(config_path).resolve()
        overrides = _load_yaml(path)
        for section, values in overrides.items():
            if section not in config:
                raise ValueError(f"Unknown configuration section: {section}")
            if section == "font":
                config["font"] = values
                continue
            if not isinstance(values, dict):
                raise ValueError(f"Invalid {section}: expected mapping")
            for key, value in values.items():
                if key not in config[section]:
                    raise ValueError(f"Unknown configuration setting: {section}.{key}")
                config[section][key] = value
        configured_font = config["font"]
        if isinstance(configured_font, str) and configured_font.strip():
            config["font"] = str(path.parent / configured_font)
    validate_calendar_config(config)
    return config


WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
POSITIONS = ("top_left", "top_right", "bottom_left", "bottom_right", "center")


def validate_calendar_config(config: dict[str, Any]) -> None:
    page = _section(config, "page")
    for key in ("width", "height"):
        _positive_number(page, key, "page")
    for key in ("margin_top", "margin_bottom", "margin_left", "margin_right"):
        _non_negative_number(page, key, "page")
    if page["margin_left"] + page["margin_right"] >= page["width"]:
        raise ValueError("Invalid page: horizontal margins leave no drawable width")
    if page["margin_top"] + page["margin_bottom"] >= page["height"]:
        raise ValueError("Invalid page: vertical margins leave no drawable height")

    title = _section(config, "title")
    weekdays = _section(config, "weekdays")
    for section, key, count in (("title", "months", 12), ("weekdays", "names", 7)):
        names = config[section].get(key)
        if (
            not isinstance(names, list)
            or len(names) != count
            or not all(
                isinstance(name, str) and name.strip() and not any(c in name for c in "\n\r\t") for name in names
            )
        ):
            raise ValueError(f"Invalid {section}.{key}: expected {count} non-empty, single-line names")
    if weekdays.get("week_start") not in WEEKDAYS:
        raise ValueError("Invalid weekdays.week_start: expected monday through sunday")
    for section, values in (("title", title), ("weekdays", weekdays)):
        _positive_number(values, "font_size", section)
        _non_negative_number(values, "gap_after", section)

    grid = _section(config, "grid")
    for key in ("gap", "border_radius"):
        _non_negative_number(grid, key, "grid")
    _positive_number(grid, "border_width", "grid")
    opacity = grid.get("empty_opacity")
    if type(opacity) not in (int, float) or not 0 <= opacity <= 1:
        raise ValueError("Invalid grid.empty_opacity: expected a number between 0 and 1")

    day = _section(config, "day_numbers")
    _positive_number(day, "font_size", "day_numbers")
    _non_negative_number(day, "padding", "day_numbers")
    if day.get("position") not in POSITIONS:
        raise ValueError(f"Invalid day_numbers.position: expected one of {', '.join(POSITIONS)}")

    for section, key in (("title", "color"), ("weekdays", "color"), ("day_numbers", "color"), ("grid", "border_color")):
        value = config[section][key]
        try:
            if not isinstance(value, str):
                raise ValueError
            toColor(value)
        except (ValueError, TypeError, AttributeError) as exc:
            raise ValueError(f"Invalid {section}.{key}: expected a color string") from exc
    font_path = config.get("font")
    if not isinstance(font_path, str) or not font_path.strip():
        raise ValueError("Invalid font: expected a non-empty file path")


def _section(config: dict[str, Any], name: str) -> dict[str, Any]:
    section = config.get(name)
    if not isinstance(section, dict):
        raise ValueError(f"Invalid {name}: expected mapping")
    return section


def _positive_number(section: dict[str, Any], key: str, section_name: str) -> None:
    value = section.get(key)
    if type(value) not in (int, float) or not isfinite(value) or value <= 0:
        raise ValueError(f"Invalid {section_name}.{key}: {value}")


def _non_negative_number(section: dict[str, Any], key: str, section_name: str) -> None:
    value = section.get(key)
    if type(value) not in (int, float) or not isfinite(value) or value < 0:
        raise ValueError(f"Invalid {section_name}.{key}: {value}")
