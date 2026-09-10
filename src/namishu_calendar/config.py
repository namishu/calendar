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


def load_config(config_path: str | Path | None = None, *, font_path: str | Path | None = None) -> dict:
    config = _load_yaml(DATA_DIR / "main.yaml")
    config["font"]["path"] = str(DATA_DIR / config["font"]["path"])
    if config_path is not None:
        path = Path(config_path).resolve()
        overrides = _load_yaml(path)
        for section, values in overrides.items():
            if section not in config:
                raise ValueError(f"Unknown configuration section: {section}")
            if not isinstance(values, dict):
                raise ValueError(f"Invalid {section}: expected mapping")
            for key, value in values.items():
                if key not in config[section]:
                    raise ValueError(f"Unknown configuration setting: {section}.{key}")
                config[section][key] = value
        configured_font = config["font"]["path"]
        if isinstance(configured_font, str) and configured_font.strip():
            config["font"]["path"] = str(path.parent / configured_font)
    if font_path is not None:
        config["font"]["path"] = str(Path(font_path).resolve())
    validate_calendar_config(config)
    return config


def validate_calendar_config(config: dict[str, Any]) -> None:
    layout = _section(config, "layout")
    _positive_number(layout, "width", "layout")
    _positive_number(layout, "height", "layout")
    for key in ("margin_top", "margin_bottom", "margin_left", "margin_right"):
        _non_negative_number(layout, key, "layout")
    if layout["margin_left"] + layout["margin_right"] >= layout["width"]:
        raise ValueError("Invalid layout: horizontal margins leave no drawable width")
    if layout["margin_top"] + layout["margin_bottom"] >= layout["height"]:
        raise ValueError("Invalid layout: vertical margins leave no drawable height")

    header = _section(config, "header")
    months = header.get("months")
    if not isinstance(months, list) or len(months) != 12 or not all(isinstance(x, str) and x.strip() for x in months):
        raise ValueError("Invalid header.months: expected 12 non-empty names")
    _positive_number(header, "size", "header")
    for key in ("padding_left", "padding_right"):
        _non_negative_number(header, key, "header")

    weekday = _section(config, "weekday")
    weekdays = weekday.get("names")
    if (
        not isinstance(weekdays, list)
        or len(weekdays) != 7
        or not all(isinstance(x, str) and x.strip() for x in weekdays)
    ):
        raise ValueError("Invalid weekday.names: expected 7 non-empty names")
    first_day = weekday.get("first_day")
    if type(first_day) is not int or not (0 <= first_day <= 6):
        raise ValueError(f"Invalid weekday.first_day: {first_day}")
    _positive_number(weekday, "size", "weekday")
    for key in ("padding_top", "padding_bottom"):
        _non_negative_number(weekday, key, "weekday")

    cell = _section(config, "cell")
    _non_negative_number(cell, "padding", "cell")
    _non_negative_number(cell, "border_radius", "cell")
    _positive_number(cell, "border_width", "cell")
    hide_empty = cell.get("hide_empty")
    if type(hide_empty) not in (int, float) or not (0 <= hide_empty <= 1):
        raise ValueError(f"Invalid cell.hide_empty: {hide_empty}")

    day = _section(config, "day")
    _positive_number(day, "size", "day")
    align = day.get("align")
    if not isinstance(align, str) or align not in {"LT", "RT", "LB", "RB", "C"}:
        raise ValueError(f"Invalid day.align: {align}")
    for key in ("padding_top", "padding_bottom", "padding_left", "padding_right"):
        _non_negative_number(day, key, "day")

    for section, key in (("header", "color"), ("weekday", "color"), ("day", "color"), ("cell", "border_color")):
        value = config[section][key]
        try:
            if not isinstance(value, str):
                raise ValueError
            toColor(value)
        except (ValueError, TypeError, AttributeError) as exc:
            raise ValueError(f"Invalid {section}.{key}: expected a color string") from exc
    font_path = _section(config, "font").get("path")
    if not isinstance(font_path, str) or not font_path.strip():
        raise ValueError("Invalid font.path: expected a non-empty file path")


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
