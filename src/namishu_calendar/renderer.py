from __future__ import annotations

from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas

from .instance import MonthCalendarInstance


class MonthCalendarRenderer:
    def __init__(self, config: dict, font_name: str):
        self.config = config
        self.font_name = font_name

    def draw_month(self, pdf: canvas.Canvas, month_data: MonthCalendarInstance) -> None:
        y0 = self._draw_header(pdf, month_data)
        y1 = self._draw_weekdays(pdf, month_data, y0)
        self._draw_cells(pdf, month_data, y1)
        self._draw_days(pdf, month_data, y1)

    def _draw_header(self, pdf: canvas.Canvas, month_data: MonthCalendarInstance) -> float:
        cfg = self.config
        header = cfg["header"]
        layout = cfg["layout"]

        font_size = header["size"]
        pdf.setFont(self.font_name, font_size)
        self._set_fill(pdf, header["color"])

        paper_height = self._mm_to_pt(layout["height"])
        paper_width = self._mm_to_pt(layout["width"])
        margin_top = self._mm_to_pt(layout["margin_top"])
        margin_left = self._mm_to_pt(layout["margin_left"])
        margin_right = self._mm_to_pt(layout["margin_right"])

        x = margin_left + self._mm_to_pt(header["padding_left"])
        y = paper_height - margin_top
        pdf.drawString(x, y, month_data.month_text())

        year_text = str(month_data.year)
        year_width = pdf.stringWidth(year_text, self.font_name, font_size)
        x = paper_width - margin_right - year_width - self._mm_to_pt(header["padding_right"])
        pdf.drawString(x, y, year_text)

        self._reset_color(pdf)
        return y

    def _draw_weekdays(self, pdf: canvas.Canvas, month_data: MonthCalendarInstance, y0: float) -> float:
        cfg = self.config
        weekday_cfg = cfg["weekday"]
        font_size = weekday_cfg["size"]
        pdf.setFont(self.font_name, font_size)
        self._set_fill(pdf, weekday_cfg["color"])

        y = y0 - self._mm_to_pt(weekday_cfg["padding_top"])
        x0 = self._mm_to_pt(cfg["layout"]["margin_left"])
        padding = self._mm_to_pt(cfg["cell"]["padding"])
        cell_width, _ = self._cell_size(month_data, y)
        weekdays = month_data.weekday_texts()
        for i in range(7):
            text_width = pdf.stringWidth(weekdays[i], self.font_name, font_size)
            x = x0 + (cell_width + padding) * i + (cell_width - text_width) / 2
            pdf.drawString(x, y, weekdays[i])

        y -= self._mm_to_pt(weekday_cfg["padding_bottom"])
        self._reset_color(pdf)
        return y

    def _draw_cells(self, pdf: canvas.Canvas, month_data: MonthCalendarInstance, y0: float) -> None:
        rows = month_data.weeks_across()
        cols = 7
        cell_width, cell_height = self._cell_size(month_data, y0)
        matrix = month_data.day_matrix()
        for i in range(rows):
            for j in range(cols):
                x, y = self._cell_pos(y0, i + 1, j + 1, month_data)
                self._draw_single_cell(pdf, matrix[i][j], x, y, cell_width, cell_height)
        self._reset_color(pdf)

    def _draw_days(self, pdf: canvas.Canvas, month_data: MonthCalendarInstance, y0: float) -> None:
        cfg = self.config
        day_cfg = cfg["day"]
        font_size = day_cfg["size"]
        pdf.setFont(self.font_name, font_size)
        self._set_fill(pdf, day_cfg["color"])

        rows = month_data.weeks_across()
        cols = 7
        cell_width, cell_height = self._cell_size(month_data, y0)
        matrix = month_data.day_matrix()

        for i in range(rows):
            for j in range(cols):
                day = matrix[i][j]
                if day == 0:
                    continue
                x, y = self._cell_pos(y0, i + 1, j + 1, month_data)
                tx, ty = self._align_day(x, y, day, font_size, cell_width, cell_height)
                pdf.drawString(tx, ty, str(day))

        self._reset_color(pdf)

    def _draw_single_cell(
        self,
        pdf: canvas.Canvas,
        day: int,
        x: float,
        y: float,
        cell_width: float,
        cell_height: float,
    ) -> None:
        cfg = self.config["cell"]
        opacity = 1.0 if day != 0 else 1.0 - cfg["hide_empty"]
        self._set_stroke(
            pdf,
            width=self._mm_to_pt(cfg["border_width"]),
            color=cfg["border_color"],
            opacity=opacity,
        )
        radius = self._mm_to_pt(cfg["border_radius"])
        pdf.roundRect(x, y, cell_width, cell_height, radius)

    def _cell_size(self, month_data: MonthCalendarInstance, y0: float) -> tuple[float, float]:
        cfg = self.config
        paper_width = self._mm_to_pt(cfg["layout"]["width"])
        margin_left = self._mm_to_pt(cfg["layout"]["margin_left"])
        margin_right = self._mm_to_pt(cfg["layout"]["margin_right"])
        margin_bottom = self._mm_to_pt(cfg["layout"]["margin_bottom"])
        padding = self._mm_to_pt(cfg["cell"]["padding"])

        columns = 7
        rows = month_data.weeks_across()
        width = (paper_width - margin_left - margin_right - padding * (columns - 1)) / columns
        height = (y0 - margin_bottom - padding * (rows - 1)) / rows
        return width, height

    def _cell_pos(
        self,
        y0: float,
        row: int,
        col: int,
        month_data: MonthCalendarInstance,
    ) -> tuple[float, float]:
        margin_left = self._mm_to_pt(self.config["layout"]["margin_left"])
        width, height = self._cell_size(month_data, y0)
        padding = self._mm_to_pt(self.config["cell"]["padding"])

        x = margin_left + (col - 1) * (width + padding)
        y = y0 - row * height - padding * (row - 1)
        return x, y

    def _align_day(
        self,
        x: float,
        y: float,
        day: int,
        font_size: float,
        cell_width: float,
        cell_height: float,
    ) -> tuple[float, float]:
        cfg = self.config["day"]
        padding_left = self._mm_to_pt(cfg["padding_left"])
        padding_bottom = self._mm_to_pt(cfg["padding_bottom"])
        padding_right = self._mm_to_pt(cfg["padding_right"])
        padding_top = self._mm_to_pt(cfg["padding_top"])

        text_width = self._text_width(str(day), font_size)
        text_height = font_size / 1.2
        align = cfg["align"]

        if align == "LT":
            x += padding_left
            y += cell_height - padding_top - text_height
        elif align == "RT":
            x += cell_width - padding_right - text_width
            y += cell_height - padding_top - text_height
        elif align == "LB":
            x += padding_left
            y += padding_bottom
        elif align == "RB":
            x += cell_width - padding_right - text_width
            y += padding_bottom
        elif align == "C":
            x += (cell_width - text_width) / 2
            y += (cell_height - text_height) / 2

        return x, y

    def _set_fill(self, pdf: canvas.Canvas, color: str, opacity: float | None = None) -> None:
        pdf.setFillColor(color, opacity)

    def _set_stroke(
        self,
        pdf: canvas.Canvas,
        width: float | None = None,
        color: str | None = None,
        opacity: float | None = None,
    ) -> None:
        if width is not None:
            pdf.setLineWidth(width)
        if color is not None:
            pdf.setStrokeColor(color, opacity)

    def _reset_color(self, pdf: canvas.Canvas) -> None:
        pdf.setFillColor("black")
        pdf.setStrokeColor("black")

    def _text_width(self, text: str, font_size: float) -> float:
        return pdfmetrics.stringWidth(text, self.font_name, font_size)

    def _mm_to_pt(self, value: float) -> float:
        return value * mm
