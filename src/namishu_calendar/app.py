from __future__ import annotations

from datetime import date
from pathlib import Path

from .config import WEEKDAYS, load_config
from .fonts import register_configured_font, validate_font_characters
from .instance import MonthCalendarInstance
from .pdf import create_canvas
from .renderer import MonthCalendarRenderer


class CalendarApp:
    """Generate calendars using a snapshot of the defaults and optional overrides."""

    def __init__(self, config_path: str | Path | None = None):
        self.config = load_config(config_path)
        self.font_name = register_configured_font(self.config["font"])
        validate_font_characters(
            self.font_name, "0123456789" + "".join(self.config["title"]["months"] + self.config["weekdays"]["names"])
        )
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

        months = [
            MonthCalendarInstance(
                year=year,
                month=current_month,
                months=self.config["title"]["months"],
                weekdays=self.config["weekdays"]["names"],
                first_day=WEEKDAYS.index(self.config["weekdays"]["week_start"]),
            )
            for current_month in (range(1, 13) if month is None else [month])
        ]
        # Validate every page before creating directories or replacing an existing PDF.
        layouts = [self.renderer.layout(item) for item in months]
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        page = self.config["page"]
        title = f"Calendar {year}" if month is None else f"Calendar {year}-{month:02d}"
        pdf = create_canvas(output, width_mm=page["width"], height_mm=page["height"], title=title)
        for item, layout in zip(months, layouts, strict=True):
            self.renderer.draw_month(pdf, item, layout)
            pdf.showPage()
        pdf.save()
        return output
