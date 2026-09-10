from __future__ import annotations

from pathlib import Path

from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def create_canvas(output_path: Path, *, width_mm: float, height_mm: float, title: str) -> canvas.Canvas:
    pdf = canvas.Canvas(str(output_path), pagesize=(width_mm * mm, height_mm * mm))
    pdf.setTitle(title)
    pdf.setAuthor("Namishu")
    pdf.setSubject("Printable monthly calendar")
    pdf.setCreator("Namishu Calendar")
    return pdf
