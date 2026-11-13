def generate_svg(stats, filename, dark=True):
    bg_color = "#0d1117" if dark else "#ffffff"
    border_color = "#30363d" if dark else "#d0d7de"
    title_color = "#e6edf3" if dark else "#1f2328"
    text_color = "#8b949e" if dark else "#656d76"

    width = 540
    height = 145
    bar_width = 480
    bar_x = 30
    bar_y = 28

    bar_segments = ""
    current_x = bar_x
    for lang, pct, color in stats:
        seg_w = (pct / 100) * bar_width
        bar_segments += f'<rect x="{current_x:.2f}" y="{bar_y}" width="{seg_w:.2f}" height="8" fill="{color}" />\n'
        current_x += seg_w

    legend_items = ""
    for idx, (lang, pct, color) in enumerate(stats):
        col = idx % 2
        row = idx // 2
        x = 30 + (col * 250)
        y = 65 + (row * 26)
        legend_items += f'''
        <circle cx="{x + 5}" cy="{y - 4}" r="4.5" fill="{color}" />
        <text x="{x + 18}" y="{y}" fill="{title_color}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="13" font-weight="500">{lang}</text>
        <text x="{x + 115}" y="{y}" fill="{text_color}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="13">{pct:.1f}%</text>
        '''

    svg_content = f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="6" fill="{bg_color}" stroke="{border_color}"/>
      
      <clipPath id="bar-clip">
        <rect x="{bar_x}" y="{bar_y}" width="{bar_width}" height="8" rx="4" />
      </clipPath>
      <g clip-path="url(#bar-clip)">
        {bar_segments}
      </g>

      {legend_items}
    </svg>'''

    with open(filename, "w", encoding="utf-8") as f:
        f.write(svg_content)
