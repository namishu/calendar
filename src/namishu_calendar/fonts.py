from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def register_configured_font(font_config: dict) -> str:
    path = Path(font_config["path"])
    # Distinct font paths must not overwrite each other's registration.
    name = "calendar-" + sha256(str(path).encode()).hexdigest()[:16]
    try:
        pdfmetrics.registerFont(TTFont(name, str(path)))
    except Exception as exc:
        raise ValueError(f"Could not load font: {path}. Provide a readable TrueType font file.") from exc
    return name
