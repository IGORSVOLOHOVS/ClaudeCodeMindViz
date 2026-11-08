# Install

1. Install [uv](https://docs.astral.sh/uv/) and Python 3.13.
2. Clone this repository and run `uv sync --frozen` at its root.

The tool itself uses only the standard library. uv brings the test tools.

`.\recipe.ps1 build` packs the module into a wheel in `dist\`. Once that wheel is installed, `python -m mmdstats` runs the tool.
