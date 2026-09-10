from pathlib import Path

import pytest
import yaml
from pypdf import PdfReader
from pypdf.generic import ContentStream
from reportlab.lib.units import mm

from namishu_calendar import CalendarApp


def _render(tmp_path: Path, overrides: dict, *, month: int = 9) -> tuple[CalendarApp, PdfReader]:
    config = tmp_path / "custom.yaml"
    config.write_text(yaml.safe_dump(overrides))
    app = CalendarApp(config)
    return app, PdfReader(app.generate(tmp_path / "calendar.pdf", year=2027, month=month))


def _text_boxes(app: CalendarApp, reader: PdfReader) -> dict[str, tuple]:
    boxes = {}

    def visit(text, cm, tm, font, size):
        text = text.rstrip("\n")
        if text:
            x0, y0, x1, y1 = app.renderer.metrics.bounds(text, size)
            boxes[text] = (tm[4] + x0, tm[5] + y0, tm[4] + x1, tm[5] + y1)

    reader.pages[0].extract_text(visitor_text=visit)
    return boxes


def _border_boxes(reader: PdfReader) -> list[tuple]:
    boxes = []
    points = []
    for operands, operator in ContentStream(reader.pages[0].get_contents(), reader).operations:
        if operator in (b"m", b"l", b"c"):
            points.extend(zip(map(float, operands[::2]), map(float, operands[1::2]), strict=True))
        elif operator == b"S":
            boxes.append(
                (
                    min(x for x, y in points),
                    min(y for x, y in points),
                    max(x for x, y in points),
                    max(y for x, y in points),
                )
            )
            points = []
    return boxes


@pytest.mark.parametrize("title_size,weekday_size", [(20, 16), (32, 17)])
def test_visible_text_spacing_and_page_margins(tmp_path: Path, title_size: int, weekday_size: int) -> None:
    app, reader = _render(
        tmp_path,
        {
            "title": {"font_size": title_size, "gap_after": 5},
            "weekdays": {"font_size": weekday_size, "gap_after": 3},
            "grid": {"gap": 4},
        },
    )
    boxes = _text_boxes(app, reader)
    titles = [boxes["SEPTEMBER"], boxes["2027"]]
    weekdays = [boxes[name] for name in app.config["weekdays"]["names"]]
    borders = _border_boxes(reader)
    half_stroke = app.config["grid"]["border_width"] * mm / 2
    assert max(b[3] for b in titles) == pytest.approx(200 * mm, abs=0.001)
    assert titles[0][0] == pytest.approx(20 * mm, abs=0.001)
    assert titles[1][2] == pytest.approx(277 * mm, abs=0.001)
    assert min(b[1] for b in titles) - max(b[3] for b in weekdays) == pytest.approx(5 * mm, abs=0.001)
    assert min(b[1] for b in weekdays) - (borders[0][3] + half_stroke) == pytest.approx(3 * mm, abs=0.001)
    assert borders[1][0] - borders[0][2] - 2 * half_stroke == pytest.approx(4 * mm, abs=0.001)
    assert min(b[1] for b in borders) - half_stroke == pytest.approx(10 * mm, abs=0.001)


@pytest.mark.parametrize("position", ["top_left", "top_right", "bottom_left", "bottom_right", "center"])
def test_day_number_position(tmp_path: Path, position: str) -> None:
    # Center must ignore padding, even when it would be too large for corner placement.
    padding = 100 if position == "center" else 3
    app, reader = _render(tmp_path, {"day_numbers": {"position": position, "padding": padding}})
    text = _text_boxes(app, reader)["1"]
    border = _border_boxes(reader)[2]  # September 1, 2027 is a Wednesday.
    half_stroke = app.config["grid"]["border_width"] * mm / 2
    if position == "center":
        assert (text[0] + text[2]) / 2 == pytest.approx((border[0] + border[2]) / 2, abs=0.001)
        assert (text[1] + text[3]) / 2 == pytest.approx((border[1] + border[3]) / 2, abs=0.001)
    else:
        horizontal = text[0] - border[0] if position.endswith("left") else border[2] - text[2]
        vertical = border[3] - text[3] if position.startswith("top") else text[1] - border[1]
        assert horizontal - half_stroke == pytest.approx(3 * mm, abs=0.001)
        assert vertical - half_stroke == pytest.approx(3 * mm, abs=0.001)


@pytest.mark.parametrize("opacity,borders", [(0, 30), (0.2, 35), (1, 35)])
def test_empty_cell_visibility(tmp_path: Path, opacity: float, borders: int) -> None:
    _, reader = _render(tmp_path, {"grid": {"empty_opacity": opacity}})
    assert len(_border_boxes(reader)) == borders
    if 0 < opacity < 1:
        states = reader.pages[0]["/Resources"]["/ExtGState"]
        assert any(float(state.get_object().get("/CA", 1)) == opacity for state in states.values())


@pytest.mark.parametrize(
    "overrides,message",
    [
        ({"grid": {"gap": 50}}, "No space"),
        ({"page": {"height": 30}}, "No space"),
        ({"title": {"gap_after": 200}}, "No space"),
        ({"title": {"font_size": 200}}, "Title does not fit"),
        ({"weekdays": {"font_size": 40}}, "Weekday names do not fit"),
        ({"day_numbers": {"font_size": 100}}, "Day numbers do not fit"),
        ({"day_numbers": {"padding": 50}}, "Day numbers do not fit"),
        ({"grid": {"border_width": 100}}, "grid.border_width"),
        ({"grid": {"border_radius": 100}}, "grid.border_radius"),
        ({"grid": {"empty_opacity": 2}}, "grid.empty_opacity"),
        ({"weekdays": {"week_start": 0}}, "weekdays.week_start"),
        ({"day_numbers": {"position": "LT"}}, "day_numbers.position"),
    ],
)
def test_invalid_layout_preserves_existing_file(tmp_path: Path, overrides: dict, message: str) -> None:
    config = tmp_path / "invalid.yaml"
    config.write_text(yaml.safe_dump(overrides))
    output = tmp_path / "existing.pdf"
    output.write_bytes(b"original contents")
    with pytest.raises(ValueError, match=message):
        CalendarApp(config).generate(output, year=2027, month=9)
    assert output.read_bytes() == b"original contents"


def test_full_year_validates_later_months_before_writing(tmp_path: Path) -> None:
    months = CalendarApp().config["title"]["months"]
    months[8] = "SEPTEMBER" * 20
    config = tmp_path / "invalid.yaml"
    config.write_text(yaml.safe_dump({"title": {"months": months}}))
    app = CalendarApp(config)
    app.generate(tmp_path / "january.pdf", year=2027, month=1)
    output = tmp_path / "new-directory/year.pdf"
    with pytest.raises(ValueError, match="Title does not fit"):
        app.generate(output, year=2027)
    assert not output.parent.exists()
