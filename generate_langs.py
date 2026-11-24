"""Entrypoint script orchestrating language metrics collection and SVG generation."""

import os
from metrics_collector import collect_all_language_stats
from svg_renderer import render_svg


def main() -> None:
    """Run metrics collection and render theme-appropriate SVGs."""
    token = os.environ.get("METRICS_TOKEN") or os.environ.get("GITHUB_TOKEN")
    assert token is None or isinstance(token, str), "Token must be string or None"

    stats = collect_all_language_stats(token)
    assert isinstance(stats, list), "Language stats must be a list"

    if len(stats) > 0:
        render_svg(stats, "langs-dark.svg", dark=True)
        render_svg(stats, "langs-light.svg", dark=False)


if __name__ == "__main__":
    main()
