from __future__ import annotations

from dataclasses import dataclass

from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from .fonts import FontMetrics
from .month import CalendarMonth


@dataclass(frozen=True)
class MonthLayout:
    left: float
    right: float
    title_baseline: float
    weekdays_baseline: float
    grid_top: float
    cell_width: float
    cell_height: float


class MonthCalendarRenderer:
    def __init__(self, config: dict, font_name: str):
        self.config = config
        self.font_name = font_name
        self.metrics = FontMetrics(font_name)

    def layout(self, month: CalendarMonth) -> MonthLayout:
        page, title, weekdays, grid, numbers = (
            self.config[key] for key in ("page", "title", "weekdays", "grid", "day_numbers")
        )
        left = page["margin_left"] * mm
        right = (page["width"] - page["margin_right"]) * mm
        width = right - left
        top = (page["height"] - page["margin_top"]) * mm
        bottom = page["margin_bottom"] * mm
        title_bounds = [self.metrics.bounds(text, title["font_size"]) for text in (month.month_text(), str(month.year))]
        if sum(b[2] - b[0] for b in title_bounds) >= width:
            raise ValueError("Title does not fit: reduce title.font_size or increase the usable page width")
        title_baseline = top - max(b[3] for b in title_bounds)
        title_bottom = title_baseline + min(b[1] for b in title_bounds)
        weekday_bounds = [self.metrics.bounds(text, weekdays["font_size"]) for text in month.weekday_texts()]
        weekdays_baseline = title_bottom - title["gap_after"] * mm - max(b[3] for b in weekday_bounds)
        grid_top = weekdays_baseline + min(b[1] for b in weekday_bounds) - weekdays["gap_after"] * mm
        gap = grid["gap"] * mm
        rows = month.row_count
        cell_width = (width - 6 * gap) / 7
        cell_height = (grid_top - bottom - (rows - 1) * gap) / rows
        if cell_width <= 0 or cell_height <= 0:
            raise ValueError(
                f"No space for the calendar grid in {month.year}-{month.month:02d}: "
                "check page dimensions, margins, gap_after, font sizes, and grid.gap"
            )
        stroke = grid["border_width"] * mm
        if stroke >= min(cell_width, cell_height):
            raise ValueError("grid.border_width is too large for the calendar cells")
        if grid["border_radius"] * mm > (min(cell_width, cell_height) - stroke) / 2:
            raise ValueError("grid.border_radius is too large for the calendar cells")
        if any(b[2] - b[0] > cell_width for b in weekday_bounds):
            raise ValueError("Weekday names do not fit: shorten weekdays.names or reduce weekdays.font_size")
        layout = MonthLayout(left, right, title_baseline, weekdays_baseline, grid_top, cell_width, cell_height)
        inset = stroke + (0 if numbers["position"] == "center" else numbers["padding"] * mm)
        for day in (day for week in month.days for day in week if day):
            x0, y0, x1, y1 = self.metrics.bounds(str(day), numbers["font_size"])
            if x1 - x0 > cell_width - 2 * inset or y1 - y0 > cell_height - 2 * inset:
                raise ValueError(
                    f"Day numbers do not fit in {month.year}-{month.month:02d}: "
                    "reduce day_numbers.font_size or padding, or increase the usable grid area"
                )
            # Keep the whole visible text box inside the rounded border's inner edge.
            radius = max(0, grid["border_radius"] * mm - stroke / 2)
            if radius:
                tx, ty = self._number_position(str(day), 0, 0, layout)
                for x in (tx + x0, tx + x1):
                    for y in (ty + y0, ty + y1):
                        dx = max(stroke + radius - x, x - (cell_width - stroke - radius), 0)
                        dy = max(stroke + radius - y, y - (cell_height - stroke - radius), 0)
                        if dx * dx + dy * dy > radius * radius + 1e-9:
                            raise ValueError(
                                "Day numbers overlap rounded corners: increase day_numbers.padding, "
                                "reduce grid.border_radius or day_numbers.font_size, or use position: center"
                            )
        return layout

    def draw_month(self, pdf: canvas.Canvas, month: CalendarMonth, layout: MonthLayout) -> None:
        title, weekdays, grid, numbers = (self.config[key] for key in ("title", "weekdays", "grid", "day_numbers"))
        pdf.saveState()
        pdf.setFont(self.font_name, title["font_size"])
        pdf.setFillColor(title["color"])
        month_bounds = self.metrics.bounds(month.month_text(), title["font_size"])
        year_bounds = self.metrics.bounds(str(month.year), title["font_size"])
        pdf.drawString(layout.left - month_bounds[0], layout.title_baseline, month.month_text())
        pdf.drawString(layout.right - year_bounds[2], layout.title_baseline, str(month.year))

        gap = grid["gap"] * mm
        pdf.setFont(self.font_name, weekdays["font_size"])
        pdf.setFillColor(weekdays["color"])
        for column, text in enumerate(month.weekday_texts()):
            bounds = self.metrics.bounds(text, weekdays["font_size"])
            center = layout.left + column * (layout.cell_width + gap) + layout.cell_width / 2
            pdf.drawString(center - (bounds[0] + bounds[2]) / 2, layout.weekdays_baseline, text)

        stroke = grid["border_width"] * mm
        pdf.setLineWidth(stroke)
        pdf.setFont(self.font_name, numbers["font_size"])
        pdf.setFillColor(numbers["color"])
        for row, week in enumerate(month.days):
            for column, day in enumerate(week):
                x = layout.left + column * (layout.cell_width + gap)
                y = layout.grid_top - (row + 1) * layout.cell_height - row * gap
                opacity = 1 if day else grid["empty_opacity"]
                if opacity:
                    pdf.setStrokeColor(grid["border_color"], alpha=opacity)
                    pdf.roundRect(
                        x + stroke / 2,
                        y + stroke / 2,
                        layout.cell_width - stroke,
                        layout.cell_height - stroke,
                        grid["border_radius"] * mm,
                    )
                if day:
                    tx, ty = self._number_position(str(day), x, y, layout)
                    pdf.drawString(tx, ty, str(day))
        pdf.restoreState()

    def _number_position(self, text: str, x: float, y: float, layout: MonthLayout) -> tuple[float, float]:
        numbers = self.config["day_numbers"]
        x0, y0, x1, y1 = self.metrics.bounds(text, numbers["font_size"])
        position = numbers["position"]
        if position == "center":
            return x + (layout.cell_width - x0 - x1) / 2, y + (layout.cell_height - y0 - y1) / 2
        inset = (self.config["grid"]["border_width"] + numbers["padding"]) * mm
        tx = x + inset - x0 if position.endswith("left") else x + layout.cell_width - inset - x1
        ty = y + layout.cell_height - inset - y1 if position.startswith("top") else y + inset - y0
        return tx, ty
