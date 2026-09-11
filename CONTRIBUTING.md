# Development

Use Python 3.10+ and uv:

```bash
uv sync --locked
uv run --frozen pytest
uv run --frozen ruff check src tests scripts
uv run --frozen ruff format --check src tests scripts
```

## Release checks

Build the source distribution and the wheel, then verify the exact wheel:

```bash
uv build
uv run python scripts/check_wheel.py dist/namishu_calendar-0.1.0-py3-none-any.whl
uvx twine check --strict dist/*
```

Use the matching wheel filename after changing the version. The checker requires
uv and the development dependencies installed by `uv sync`. It does not build a
package or publish anything. It rejects missing resources and licenses, creates a
temporary environment with only the wheel and its runtime dependencies, and runs
the installed command outside the checkout. PDF inspection runs in the development
environment, so it cannot supply missing dependencies to the installed application.

Calendar checks cover the bundled Noto Sans font and its embedding, CLI version
and help, leap-year February dates, all 12 months of a year, and A4 landscape pages.

Ordinary `uv run pytest` runs functional tests without building distributions or
creating installation environments. CI tests Python 3.10 and 3.14 on Linux, macOS,
and Windows, builds one sdist and its wheel, checks them with Twine, and verifies
the same wheel on all six platform/Python combinations. Only a non-prerelease
GitHub Release with a tag matching the package version (`vVERSION`) publishes to
PyPI. Publishing downloads the verified artifacts and does not rebuild them.
The repository's PyPI trusted publisher and `pypi` environment must be configured
for this workflow. Pushes to main, pull requests, and manual runs verify only.
