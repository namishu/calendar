<h1 align="center">Namishu Calendar</h1>

<p align="center">Printable monthly calendars, ready for your plans.</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&amp;logo=python&amp;logoColor=white" alt="Python 3.10+">
  <a href="https://github.com/namishu/calendar/blob/main/LICENSE"><img src="https://img.shields.io/badge/Code-MIT-22A06B?style=flat" alt="Code: MIT"></a>
  <img src="https://img.shields.io/badge/PDF-A4_landscape-E05D44?style=flat" alt="PDF: A4 landscape">
</p>

<p align="center"><strong>English</strong> · <a href="README.zh-CN.md">简体中文</a></p>

Namishu Calendar creates a clean monthly calendar with space for handwritten plans,
appointments, and reminders. Generate a full year or a single month as a PDF,
with one month per page. The default layout uses A4 landscape paper, English month
and weekday names, and weeks starting on Monday.

<p align="center">
  <a href="https://github.com/namishu/calendar/blob/main/examples/calendar.pdf">
    <img src="examples/calendar.png" alt="September 2027 calendar, with a Monday-first grid and space to write in each day" width="800">
  </a>
</p>

[Download the sample PDF](https://github.com/namishu/calendar/raw/refs/heads/main/examples/calendar.pdf).
Print at actual size on A4 paper.

## Installation

Requires **Python 3.10+**.

Install with either uv or pip:

```bash
uv tool install namishu-calendar
```

```bash
python -m pip install namishu-calendar
```

Both methods provide the `namishu-calendar` command. The default font and layout
are included; no separate font installation is needed.

## Quick start

Generate the **current year**, January through December, as `calendar.pdf`:

```bash
namishu-calendar
```

Choose a different year:

```bash
namishu-calendar --year 2027
```

Generate **one month** by adding `--month`:

```bash
namishu-calendar --year 2027 --month 9
```

Omit `--year` to use the current year. Choose a different output path with `-o`:

```bash
namishu-calendar --year 2027 --month 9 -o calendars/september.pdf
```

The command prints the saved file location and page count. Relative paths are
resolved from your current directory; parent directories are created as needed.
An existing PDF at the output path is replaced.

## Options

| Option | Purpose | Default |
|---|---|---|
| `--year YEAR` | Year from 1 to 9999 | Current year |
| `--month MONTH` | Generate just this month, from 1 to 12 | All 12 months |
| `-o, --output PATH` | PDF file location | `calendar.pdf` |
| `--config PATH` | YAML file with layout or font overrides | Built-in settings |
| `--help` | Show usage | |
| `--version` | Show the installed version | |

## Customize the calendar

Write only the settings you want to change. Save this as `calendar.yaml` to start
weeks on Sunday and use narrower side margins:

```yaml
weekday:
  first_day: 6
layout:
  margin_left: 15
  margin_right: 15
```

```bash
namishu-calendar --year 2027 --month 9 --config calendar.yaml
```

Unspecified settings keep their defaults, including the bundled font.
Download the [complete example configuration](https://github.com/namishu/calendar/blob/main/examples/calendar.yaml)
for all settings and comments. It works as downloaded with the bundled font;
edit it and pass its local path to `--config`.

| Setting | How to customize it |
|---|---|
| Paper and margins | `layout`: dimensions and margins in millimeters |
| Month labels | `header.months`: 12 names, January through December |
| Weekday labels | `weekday.names`: 7 names, Monday through Sunday |
| First weekday | `weekday.first_day`: `0` for Monday through `6` for Sunday |
| Text | `size` in points and `color`, for `header`, `weekday`, and `day` |
| Day boxes | `cell`: spacing, border width, radius, and border color |
| Empty boxes | `cell.hide_empty`: `0` for a full border, `1` for invisible |
| Day number position | `day.align`: `LT`, `RT`, `LB`, `RB`, or `C` for the corners or center |
| Custom font | `font.path`: a TrueType font path, relative to the YAML file or absolute |

Distances other than font sizes are in millimeters. Quote hex colors, such as
`"#5f667e"`. Month and weekday names can be translated; the included Noto Sans SC
font supports Simplified Chinese. Custom fonts must contain the characters you use.
Invalid settings or an unreadable font produce an error.

## License

Code and original documentation use the [MIT License](https://github.com/namishu/calendar/blob/main/LICENSE).
The bundled Noto Sans SC font uses the
[SIL Open Font License 1.1](https://github.com/namishu/calendar/blob/main/src/namishu_calendar/data/fonts/OFL.txt);
its [notice](https://github.com/namishu/calendar/blob/main/src/namishu_calendar/data/fonts/NOTICE.txt)
records the font's attribution and source information.
Generated calendars may be printed, shared, modified, and sold.
