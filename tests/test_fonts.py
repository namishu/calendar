from pathlib import Path

import pytest
import yaml
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from pypdf import PdfReader

from namishu_calendar import CalendarApp
from namishu_calendar.config import DATA_DIR, load_config
from namishu_calendar.fonts import FontMetrics, register_configured_font


@pytest.mark.parametrize("text", [" ", "  Hg  ", "gy", "éÉ", "0123456789", "28"])
@pytest.mark.parametrize("size", [16, 32])
def test_visible_bounds_against_fonttools(text: str, size: int) -> None:
    path = DATA_DIR / "NotoSans-Light.ttf"
    actual = FontMetrics(register_configured_font(path)).bounds(text, size)
    # Independent outline traversal, rather than the production glyf-header reader.
    with TTFont(path) as font:
        glyphs = font.getGlyphSet()
        cmap = font.getBestCmap()
        advance = 0
        boxes = []
        for char in text:
            glyph = glyphs[cmap[ord(char)]]
            pen = BoundsPen(glyphs)
            glyph.draw(pen)
            if pen.bounds:
                x0, y0, x1, y1 = pen.bounds
                boxes.append((advance + x0, y0, advance + x1, y1))
            advance += glyph.width
        expected = (
            (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
            if boxes
            else (0, 0, advance, 0)
        )
        scale = size / font["head"].unitsPerEm
        assert actual == pytest.approx(tuple(value * scale for value in expected), abs=0.05)


def test_chinese_labels_with_custom_font(tmp_path: Path) -> None:
    config = load_config()
    labels = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    characters = sorted(set("0123456789" + "".join(config["title"]["months"] + labels)))
    # Original synthetic box glyphs test Unicode embedding without distributing another font.
    names = [".notdef", *[f"uni{ord(c):04X}" for c in characters]]
    builder = FontBuilder(1000, isTTF=True)
    builder.setupGlyphOrder(names)
    builder.setupCharacterMap(dict(zip(map(ord, characters), names[1:], strict=True)))
    glyphs = {}
    for name in names:
        pen = TTGlyphPen(None)
        pen.moveTo((50, 0))
        pen.lineTo((450, 0))
        pen.lineTo((450, 700))
        pen.lineTo((50, 700))
        pen.closePath()
        glyphs[name] = pen.glyph()
    builder.setupGlyf(glyphs)
    builder.setupHorizontalMetrics(dict.fromkeys(names, (500, 50)))
    builder.setupHorizontalHeader(ascent=800, descent=-200)
    builder.setupNameTable({"familyName": "CalendarTest", "styleName": "Regular", "psName": "CalendarTest-Regular"})
    builder.setupOS2(sTypoAscender=800, sTypoDescender=-200, usWinAscent=800, usWinDescent=200)
    builder.setupPost()
    builder.setupMaxp()
    builder.save(tmp_path / "chinese.ttf")
    path = tmp_path / "config.yaml"
    path.write_text(
        yaml.safe_dump({"font": "chinese.ttf", "weekdays": {"names": labels}}, allow_unicode=True), encoding="utf-8"
    )
    page = PdfReader(CalendarApp(path).generate(tmp_path / "chinese.pdf", year=2027, month=9)).pages[0]
    assert all(label in page.extract_text() for label in labels)
    fonts = [font.get_object() for font in page["/Resources"]["/Font"].values()]
    assert any(
        "CalendarTest-Regular" in font["/BaseFont"] and "/FontFile2" in font.get("/FontDescriptor", {})
        for font in fonts
    )
