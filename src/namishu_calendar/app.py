from __future__ import annotations

from datetime import date
from pathlib import Path

from .config import load_config
from .fonts import register_configured_font
from .instance import MonthCalendarInstance
from .pdf import create_canvas
from .renderer import MonthCalendarRenderer


class CalendarApp:
    """Generate calendars using a snapshot of the defaults and optional overrides."""

    def __init__(self, config_path: str | Path | None = None):
        self.config = load_config(config_path)
        self.font_name = register_configured_font(self.config["font"])
        self.renderer = MonthCalendarRenderer(self.config, self.font_name)

    def generate(
        self,
        output_path: str | Path = "calendar.pdf",
        year: int | None = None,
        month: int | None = None,
    ) -> Path:
        """Write a full year, or a single month when month is supplied."""
        year = date.today().year if year is None else year
        if type(year) is not int or not 1 <= year <= 9999:
            raise ValueError("Invalid year: expected an integer between 1 and 9999")
        if month is not None and (type(month) is not int or not 1 <= month <= 12):
            raise ValueError("Invalid month: expected an integer between 1 and 12")

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        layout = self.config["layout"]
        title = f"Calendar {year}" if month is None else f"Calendar {year}-{month:02d}"
        pdf = create_canvas(output, width_mm=layout["width"], height_mm=layout["height"], title=title)
        for current_month in range(1, 13) if month is None else [month]:
            month_data = MonthCalendarInstance(
                year=year,
                month=current_month,
                months=self.config["header"]["months"],
                weekdays=self.config["weekday"]["names"],
                first_day=self.config["weekday"]["first_day"],
            )
            self.renderer.draw_month(pdf, month_data)
            pdf.showPage()
        pdf.save()
        return output
