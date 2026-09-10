from __future__ import annotations

import argparse
from importlib.metadata import version

from . import CalendarApp


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="namishu-calendar",
        description="Create a printable calendar PDF: a full year, or one month with --month.",
        allow_abbrev=False,
    )
    parser.add_argument("--year", type=int, metavar="YEAR", help="year, 1–9999 (default: current year)")
    parser.add_argument("--month", type=int, metavar="MONTH", help="generate one month, 1–12 (default: full year)")
    parser.add_argument(
        "-o", "--output", default="calendar.pdf", metavar="PATH", help="output PDF (default: calendar.pdf)"
    )
    parser.add_argument("--config", metavar="PATH", help="YAML overrides for the built-in layout and font")
    parser.add_argument("--font", metavar="PATH", help="TrueType font file (overrides the YAML font setting)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {version('namishu-calendar')}")
    args = parser.parse_args()

    if args.year is not None and not 1 <= args.year <= 9999:
        parser.error("--year must be between 1 and 9999")
    if args.month is not None and not 1 <= args.month <= 12:
        parser.error("--month must be between 1 and 12")
    try:
        output = CalendarApp(config_path=args.config, font_path=args.font).generate(
            output_path=args.output, year=args.year, month=args.month
        )
    except (ValueError, OSError) as exc:
        parser.exit(1, f"{parser.prog}: error: {exc}\n")
    pages = "1 page" if args.month is not None else "12 pages"
    print(f"Created {output.resolve()} ({pages})")


if __name__ == "__main__":
    main()
