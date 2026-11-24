"""SVG generation and rendering layer for language metrics."""

LANG_COLORS = {
    "TypeScript": "#3178c6",
    "JavaScript": "#f1e05a",
    "Java": "#b07219",
    "Prolog": "#74283c",
    "C": "#555555",
    "C++": "#f34b7d",
    "Python": "#3572A5",
    "Assembly": "#6E4C13",
    "Rust": "#dea584",
    "CSS": "#563d7c",
    "HTML": "#e34c26",
    "Shell": "#89e051",
    "Go": "#00ADD8",
    "C#": "#178600",
    "Kotlin": "#A97BFF",
    "Swift": "#F05138",
    "SQL": "#e38c00",
    "R": "#276DC3",
    "Dart": "#00B4AB",
    "Scala": "#c22d40",
    "PHP": "#4F5D95",
    "Ruby": "#701516",
}
DEFAULT_COLOR = "#8b949e"


def build_svg_bars(stats: list[tuple[str, float]], bar_x: float, bar_y: float, bar_w: float) -> str:
    """Generate SVG rect elements for the language distribution bar."""
    assert isinstance(stats, list), "stats must be a list"
    assert bar_w > 0, "bar_width must be positive"

    segments = []
    current_x = bar_x
    for idx, (lang, pct) in enumerate(stats):
        if idx >= 50:
            break
        color = LANG_COLORS.get(lang, DEFAULT_COLOR)
        seg_w = (pct / 100.0) * bar_w
        rect = f'<rect x="{current_x:.2f}" y="{bar_y}" width="{seg_w:.2f}" height="8" fill="{color}" />'
        segments.append(rect)
        current_x += seg_w
    return "\n        ".join(segments)


def build_svg_legend(stats: list[tuple[str, float]], title_color: str, text_color: str) -> str:
    """Generate SVG legend circles and text entries for all languages."""
    assert isinstance(stats, list), "stats must be a list"
    assert isinstance(title_color, str) and len(title_color) > 0, "title_color required"

    items = []
    for idx, (lang, pct) in enumerate(stats):
        if idx >= 50:
            break
        color = LANG_COLORS.get(lang, DEFAULT_COLOR)
        col = idx % 2
        row = idx // 2
        x = 30 + (col * 250)
        y = 65 + (row * 26)
        entry = (
            f'<circle cx="{x + 5}" cy="{y - 4}" r="4.5" fill="{color}" />\n'
            f'        <text x="{x + 18}" y="{y}" fill="{title_color}" '
            f'font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Helvetica, Arial, sans-serif" '
            f'font-size="13" font-weight="500">{lang}</text>\n'
            f'        <text x="{x + 130}" y="{y}" fill="{text_color}" '
            f'font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Helvetica, Arial, sans-serif" '
            f'font-size="13">{pct:.1f}%</text>'
        )
        items.append(entry)
    return "\n        ".join(items)


def render_svg(stats: list[tuple[str, float]], filename: str, dark: bool = True) -> None:
    """Write complete SVG file representing all tracked languages."""
    assert isinstance(stats, list), "stats must be a list"
    assert isinstance(filename, str) and filename.endswith(".svg"), "Valid .svg filename required"

    bg_color = "#0d1117" if dark else "#ffffff"
    border_color = "#30363d" if dark else "#d0d7de"
    title_color = "#e6edf3" if dark else "#1f2328"
    text_color = "#8b949e" if dark else "#656d76"

    width = 540
    num_rows = max(1, (len(stats) + 1) // 2)
    height = max(145, 65 + (num_rows * 26) + 12)
    bar_width = 480
    bar_x = 30
    bar_y = 28

    bars = build_svg_bars(stats, bar_x, bar_y, bar_width)
    legend = build_svg_legend(stats, title_color, text_color)

    svg_content = f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="6" fill="{bg_color}" stroke="{border_color}"/>
      <clipPath id="bar-clip">
        <rect x="{bar_x}" y="{bar_y}" width="{bar_width}" height="8" rx="4" />
      </clipPath>
      <g clip-path="url(#bar-clip)">
        {bars}
      </g>
      {legend}
    </svg>'''

    with open(filename, "w", encoding="utf-8") as f:
        f.write(svg_content)
