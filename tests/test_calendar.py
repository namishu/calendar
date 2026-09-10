from datetime import date
from pathlib import Path

import pytest
from pypdf import PdfReader
from reportlab.lib.units import mm

from namishu_calendar import CalendarApp
from namishu_calendar.config import DATA_DIR
from namishu_calendar.instance import MonthCalendarInstance


def test_full_year_pdf(tmp_path: Path) -> None:
    output = CalendarApp().generate(tmp_path / "nested/year.pdf", year=2027)
    reader = PdfReader(output)
    assert len(reader.pages) == 12
    for page, month in zip(reader.pages, CalendarApp().config["title"]["months"], strict=True):
        text = page.extract_text()
        assert month in text
        assert "2027" in text
        assert float(page.mediabox.width) == pytest.approx(297 * mm, abs=0.01)
        assert float(page.mediabox.height) == pytest.approx(210 * mm, abs=0.01)
    assert reader.metadata.title == "Calendar 2027"


def test_single_month_pdf(tmp_path: Path) -> None:
    reader = PdfReader(CalendarApp().generate(tmp_path / "february.pdf", year=2024, month=2))
    assert len(reader.pages) == 1
    lines = reader.pages[0].extract_text().splitlines()
    assert "FEBRUARY" in lines
    assert [int(line) for line in lines if line.isdigit() and len(line) <= 2] == list(range(1, 30))


def test_current_year(tmp_path: Path) -> None:
    reader = PdfReader(CalendarApp().generate(tmp_path / "today.pdf", month=9))
    assert str(date.today().year) in reader.pages[0].extract_text()


@pytest.mark.parametrize("year,month,first_day,rows", [(2021, 2, 0, 4), (2024, 2, 6, 5), (2027, 5, 0, 6)])
def test_month_grid(year: int, month: int, first_day: int, rows: int) -> None:
    cfg = CalendarApp().config
    instance = MonthCalendarInstance(year, month, cfg["title"]["months"], cfg["weekdays"]["names"], first_day)
    assert instance.weeks_across() == rows
    assert len(instance.day_matrix()) == rows
    column = (date(year, month, 1).weekday() - first_day) % 7
    assert instance.day_matrix()[0][column] == 1
    assert instance.weekday_texts()[0] == cfg["weekdays"]["names"][first_day]


def test_partial_config_keeps_bundled_font(tmp_path: Path) -> None:
    config = tmp_path / "custom.yaml"
    config.write_text("weekdays:\n  week_start: sunday\n")
    app = CalendarApp(config)
    assert Path(app.config["font"]) == DATA_DIR / "NotoSans-Light.ttf"
    page = PdfReader(app.generate(tmp_path / "custom.pdf", year=2027, month=9)).pages[0]
    text = page.extract_text()
    assert text.index("Sunday") < text.index("Monday")
    fonts = [font.get_object() for font in page["/Resources"]["/Font"].values()]
    assert any("/FontFile2" in font.get("/FontDescriptor", {}) for font in fonts)


def test_relative_custom_font(tmp_path: Path, monkeypatch) -> None:
    directory = tmp_path / "settings"
    directory.mkdir()
    (directory / "font.ttf").symlink_to(DATA_DIR / "NotoSans-Light.ttf")
    (directory / "custom.yaml").write_text("font: font.ttf\n")
    monkeypatch.chdir(tmp_path)
    app = CalendarApp("settings/custom.yaml")
    assert Path(app.config["font"]) == directory / "font.ttf"
    assert len(PdfReader(app.generate("custom.pdf", month=9)).pages) == 1


def test_config_is_a_snapshot(tmp_path: Path) -> None:
    config = tmp_path / "settings.yaml"
    config.write_text("weekdays:\n  week_start: sunday\n")
    app = CalendarApp(config)
    config.write_text("weekdays:\n  week_start: monday\n")
    assert app.config["weekdays"]["week_start"] == "sunday"
    assert CalendarApp(config).config["weekdays"]["week_start"] == "monday"


@pytest.mark.parametrize("kwargs", [{"year": 0}, {"year": 10000}, {"year": True}, {"month": 0}, {"month": 13}])
def test_invalid_dates_do_not_create_output(tmp_path: Path, kwargs: dict) -> None:
    output = tmp_path / "invalid.pdf"
    with pytest.raises(ValueError):
        CalendarApp().generate(output, **kwargs)
    assert not output.exists()
