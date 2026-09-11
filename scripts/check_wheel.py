"""Verify an explicit wheel in an isolated installation outside the checkout."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import zipfile
from collections.abc import Callable
from email.parser import Parser
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

PACKAGE = "namishu_calendar"
COMMAND = "namishu-calendar"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_pdf(path: Path, pages: int) -> PdfReader:
    require(path.is_file() and path.stat().st_size > 0, f"Missing or empty PDF: {path.name}")
    reader = PdfReader(path)
    require(len(reader.pages) == pages, f"{path.name}: expected {pages} pages")
    for number, page in enumerate(reader.pages, start=1):
        require(
            abs(float(page.mediabox.width) - 297 * 72 / 25.4) < 0.01
            and abs(float(page.mediabox.height) - 210 * 72 / 25.4) < 0.01,
            f"{path.name}, page {number}: unexpected paper size",
        )
        fonts = [font.get_object() for font in page["/Resources"]["/Font"].values()]
        embedded = False
        for font in fonts:
            descriptor = font.get("/FontDescriptor")
            if descriptor is not None and "NotoSans" in str(font.get("/BaseFont", "")):
                stream = descriptor.get_object().get("/FontFile2")
                embedded |= stream is not None and bool(stream.get_object().get_data())
        require(embedded, f"{path.name}, page {number}: Noto Sans font is not embedded")
    return reader


def verify_cli(run_cli: Callable[..., str], folder: Path) -> None:
    run_cli("--year", "2024", "--month", "2", "--output", "february.pdf")
    reader = read_pdf(folder / "february.pdf", 1)
    lines = [line.strip() for line in reader.pages[0].extract_text().splitlines()]
    require("FEBRUARY" in lines and "2024" in lines, "Missing February 2024 heading")
    days = [int(line) for line in lines if line.isdigit() and len(line) <= 2]
    require(days == list(range(1, 30)), "Leap-year February dates are incorrect")

    run_cli("--year", "2027", "--output", "year.pdf")
    reader = read_pdf(folder / "year.pdf", 12)
    months = [
        "JANUARY",
        "FEBRUARY",
        "MARCH",
        "APRIL",
        "MAY",
        "JUNE",
        "JULY",
        "AUGUST",
        "SEPTEMBER",
        "OCTOBER",
        "NOVEMBER",
        "DECEMBER",
    ]
    day_counts = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    for page, month, count in zip(reader.pages, months, day_counts, strict=True):
        lines = [line.strip() for line in page.extract_text().splitlines()]
        require(month in lines and "2027" in lines, f"Incorrect year calendar heading: {month}")
        days = [int(line) for line in lines if line.isdigit() and len(line) <= 2]
        require(days == list(range(1, count + 1)), f"Incorrect dates for {month} 2027")
    print("Calendar: leap-year February and 12-month year verified on A4 landscape pages.")


def check_wheel(wheel: Path) -> None:
    require(wheel.is_file() and wheel.suffix == ".whl", f"Wheel does not exist: {wheel}")
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        metadata_paths = [name for name in names if name.endswith(".dist-info/METADATA")]
        require(len(metadata_paths) == 1, "Expected one distribution metadata file")
        metadata_path = metadata_paths[0]
        metadata = Parser().parsestr(archive.read(metadata_path).decode("utf-8"))
        require(metadata["Name"] == COMMAND, "Unexpected distribution name")
        require(bool(metadata["Version"]), "Missing distribution version")
        license_dir = metadata_path.removesuffix("METADATA") + "licenses/"
        for resource in [
            f"{PACKAGE}/data/default.yaml",
            f"{PACKAGE}/data/NotoSans-Light.ttf",
            f"{PACKAGE}/data/OFL.txt",
            license_dir + "LICENSE",
            license_dir + f"src/{PACKAGE}/data/OFL.txt",
        ]:
            require(resource in names, f"Missing packaged resource: {resource}")
            require(bool(archive.read(resource)), f"Empty packaged resource: {resource}")

    with tempfile.TemporaryDirectory(prefix=COMMAND + "-wheel-") as directory:
        folder = Path(directory).resolve()
        env_dir = folder / "env"
        env = os.environ.copy()
        for key in ["PYTHONPATH", "PYTHONHOME"]:
            env.pop(key, None)
        env["PYTHONNOUSERSITE"] = "1"
        subprocess.run(
            ["uv", "venv", "--python", sys.executable, str(env_dir)],
            cwd=folder,
            env=env,
            check=True,
            timeout=120,
        )
        bin_dir = env_dir / ("Scripts" if os.name == "nt" else "bin")
        python = bin_dir / ("python.exe" if os.name == "nt" else "python")
        command = bin_dir / (COMMAND + (".exe" if os.name == "nt" else ""))
        subprocess.run(
            ["uv", "pip", "install", "--python", str(python), str(wheel)],
            cwd=folder,
            env=env,
            check=True,
            timeout=300,
        )
        # Confirm Python loads the installed package, never an editable checkout.
        result = subprocess.run(
            [str(python), "-I", "-c", f"import {PACKAGE}; print({PACKAGE}.__file__)"],
            cwd=folder,
            env=env,
            capture_output=True,
            text=True,
            check=True,
            timeout=60,
        )
        require(
            Path(result.stdout.strip()).resolve().is_relative_to(env_dir),
            "Package imported outside isolated environment",
        )

        def run_cli(*args: str) -> str:
            result = subprocess.run(
                [str(command), *args], cwd=folder, env=env, capture_output=True, text=True, timeout=120
            )
            require(result.returncode == 0, f"{COMMAND} {' '.join(args)} failed:\n{result.stdout}\n{result.stderr}")
            return result.stdout

        require(
            run_cli("--version").strip() == f"{COMMAND} {metadata['Version']}",
            "CLI version does not match wheel metadata",
        )
        require("--config" in run_cli("--help"), "Installed CLI help is incomplete")
        verify_cli(run_cli, folder)
        print(f"Verified {wheel.name}: resources, licenses, isolated CLI, embedded font, and PDF contents.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path, help="Exact path to the wheel to verify")
    args = parser.parse_args()
    try:
        check_wheel(args.wheel.resolve())
    except (ValueError, OSError, subprocess.SubprocessError, zipfile.BadZipFile, PdfReadError) as exc:
        parser.exit(1, f"Wheel verification failed: {exc}\n")


if __name__ == "__main__":
    main()
