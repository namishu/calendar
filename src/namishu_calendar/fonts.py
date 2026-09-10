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


def validate_font_characters(font_name: str, text: str) -> None:
    glyphs = pdfmetrics.getFont(font_name).face.charToGlyph
    missing = sorted({char for char in text if not glyphs.get(ord(char))})
    if missing:
        codes = ", ".join(f"U+{ord(char):04X}" for char in missing[:8])
        raise ValueError(
            f"The selected font is missing characters ({codes}). "
            "Choose a font that supports your labels using font.path in your YAML configuration."
        )
