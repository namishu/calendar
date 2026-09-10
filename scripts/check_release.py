"""Build and test an installed wheel: uv run python scripts/check_release.py [--offline]."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify release artifacts without publishing them.")
    parser.add_argument("--offline", action="store_true", help="use only cached build and test dependencies")
    parser.add_argument("--dist-dir", type=Path, help="retain verified distributions in an empty directory")
    args = parser.parse_args()
    if args.dist_dir is not None:
        args.dist_dir = args.dist_dir.resolve()
        if args.dist_dir.exists() and (not args.dist_dir.is_dir() or any(args.dist_dir.iterdir())):
            parser.error("--dist-dir must be absent or an empty directory")
    uv = shutil.which("uv")
    if uv is None:
        parser.error("uv must be installed and available on PATH")
    root = Path(__file__).resolve().parents[1]
    environment = os.environ.copy()
    for key in ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV"):
        environment.pop(key, None)
    if args.offline:
        environment["UV_OFFLINE"] = "1"

    def run(*command: str | Path, cwd: Path = root) -> None:
        subprocess.run([str(part) for part in command], cwd=cwd, env=environment, check=True, timeout=300)

    with TemporaryDirectory(prefix="calendar-release-") as directory:
        work = Path(directory)
        dist = work / "dist"
        requirements = work / "tests.txt"
        run(uv, "export", "--frozen", "--only-group", "dev", "--no-emit-project", "--output-file", requirements)
        # uv builds the wheel from the sdist, checking both distribution formats.
        run(uv, "build", "--out-dir", dist)
        (wheel,) = dist.glob("*.whl")
        venv = work / "venv"
        run(uv, "venv", "--python", sys.executable, venv)
        scripts = venv / ("Scripts" if os.name == "nt" else "bin")
        python = scripts / ("python.exe" if os.name == "nt" else "python")
        cli = scripts / ("namishu-calendar.exe" if os.name == "nt" else "namishu-calendar")
        run(uv, "pip", "install", "--python", python, wheel, "-r", requirements)
        check = work / "check"
        shutil.copytree(root / "tests", check / "tests", ignore=shutil.ignore_patterns("__pycache__"))
        run(cli, "--version", cwd=check)
        run(cli, "--year", "2027", "--month", "9", "--output", "entrypoint.pdf", cwd=check)
        run(
            python,
            "-c",
            "from pathlib import Path; import sys, namishu_calendar; from pypdf import PdfReader; "
            "assert Path(namishu_calendar.__file__).is_relative_to(Path(sys.prefix)); "
            "assert len(PdfReader('entrypoint.pdf').pages) == 1",
            cwd=check,
        )
        run(python, "-m", "pytest", "-q", "tests", cwd=check)
        if args.dist_dir is not None:
            args.dist_dir.mkdir(parents=True, exist_ok=True)
            for artifact in dist.iterdir():
                shutil.copyfile(artifact, args.dist_dir / artifact.name)
    print("Release verification passed: sdist, wheel, installed command, and isolated test suite.")


if __name__ == "__main__":
    main()
