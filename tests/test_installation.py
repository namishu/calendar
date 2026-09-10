import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest
from pypdf import PdfReader


def run_cli(tmp_path: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "namishu_calendar", *args], cwd=tmp_path, capture_output=True, text=True
    )


@pytest.mark.parametrize(
    "args,pages,year",
    [
        ((), 12, None),
        (("--year", "2027"), 12, 2027),
        (("--month", "9"), 1, None),
        (("--year", "2027", "--month", "9"), 1, 2027),
    ],
)
def test_cli_defaults(tmp_path: Path, args: tuple, pages: int, year: int | None) -> None:
    result = run_cli(tmp_path, *args)
    assert result.returncode == 0, result.stderr
    output = tmp_path / "calendar.pdf"
    reader = PdfReader(output)
    assert len(reader.pages) == pages
    assert str(year or date.today().year) in reader.pages[0].extract_text()
    assert str(output) in result.stdout
    assert f"({pages} page" in result.stdout


def test_output_and_overwrite(tmp_path: Path) -> None:
    args = ("--month", "9", "-o", "nested/custom.pdf")
    assert run_cli(tmp_path, *args).returncode == 0
    assert run_cli(tmp_path, *args).returncode == 0
    assert len(PdfReader(tmp_path / "nested/custom.pdf").pages) == 1


@pytest.mark.parametrize("args", [("--month", "13"), ("--year", "10000"), ("--count", "2")])
def test_invalid_arguments(tmp_path: Path, args: tuple) -> None:
    result = run_cli(tmp_path, *args)
    assert result.returncode == 2
    assert "Traceback" not in result.stderr
    assert not (tmp_path / "calendar.pdf").exists()


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
        ("font: missing.ttf", "Could not load font"),
        ("font: null", "Invalid font"),
        ("font: {}", "Invalid font"),
        ('font: ""', "Invalid font"),
        ("weekdays:\n  firstday: 6", "Unknown configuration setting"),
    ],
)
def test_config_errors(tmp_path: Path, config: str, message: str) -> None:
    (tmp_path / "custom.yaml").write_text(config)
    result = run_cli(tmp_path, "--config", "custom.yaml")
    assert result.returncode == 1
    assert message in result.stderr
    assert "Traceback" not in result.stderr
    assert not (tmp_path / "calendar.pdf").exists()


def test_missing_config(tmp_path: Path) -> None:
    result = run_cli(tmp_path, "--config", "missing.yaml")
    assert result.returncode == 1
    assert "missing.yaml" in result.stderr
    assert "Traceback" not in result.stderr


def test_help_and_version(tmp_path: Path) -> None:
    for option in ("--help", "--version"):
        result = run_cli(tmp_path, option)
        assert result.returncode == 0
        assert "namishu-calendar" in result.stdout
        assert "--count" not in result.stdout
        assert "--font" not in result.stdout
    assert not (tmp_path / "calendar.pdf").exists()


def test_yaml_custom_font_relative_to_config(tmp_path: Path) -> None:
    import shutil

    import reportlab

    font = Path(reportlab.__file__).parent / "fonts/Vera.ttf"
    settings = tmp_path / "settings"
    settings.mkdir()
    (settings / "fonts").mkdir()
    shutil.copyfile(font, settings / "fonts/custom.ttf")
    (settings / "calendar.yaml").write_text("font: fonts/custom.ttf\n")
    result = run_cli(tmp_path, "--month", "9", "--config", "settings/calendar.yaml")
    assert result.returncode == 0, result.stderr
    page = PdfReader(tmp_path / "calendar.pdf").pages[0]
    fonts = [font.get_object() for font in page["/Resources"]["/Font"].values()]
    assert any("BitstreamVeraSans" in font["/BaseFont"] for font in fonts)


def test_chinese_labels_require_custom_font(tmp_path: Path) -> None:
    (tmp_path / "chinese.yaml").write_text(
        "weekdays:\n  names: [周一, 周二, 周三, 周四, 周五, 周六, 周日]\n", encoding="utf-8"
    )
    result = run_cli(tmp_path, "--config", "chinese.yaml", "--month", "9")
    assert result.returncode == 1
    assert "missing characters" in result.stderr
    assert "font: path/to/font.ttf" in result.stderr
    assert "Traceback" not in result.stderr
    assert not (tmp_path / "calendar.pdf").exists()
