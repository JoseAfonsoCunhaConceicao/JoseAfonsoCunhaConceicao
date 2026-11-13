import os
import requests
from collections import defaultdict

USERNAME = "JoseAfonsoCunhaConceicao"
TOKEN = os.environ.get("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {TOKEN}"} if TOKEN else {}

# Mapeamento de extensões para linguagens e cores oficiais do GitHub
EXT_MAP = {
    ".py": ("Python", "#3572A5"),
    ".c": ("C", "#555555"),
    ".h": ("C", "#555555"),
    ".cpp": ("C++", "#f34b7d"),
    ".hpp": ("C++", "#f34b7d"),
    ".rs": ("Rust", "#dea584"),
    ".ts": ("TypeScript", "#3178c6"),
    ".tsx": ("TypeScript", "#3178c6"),
    ".js": ("JavaScript", "#f1e05a"),
    ".jsx": ("JavaScript", "#f1e05a"),
    ".java": ("Java", "#b07219"),
    ".go": ("Go", "#00ADD8"),
    ".cs": ("C#", "#178600"),
    ".asm": ("Assembly", "#6E4C13"),
    ".s": ("Assembly", "#6E4C13"),
    ".html": ("HTML", "#e34c26"),
    ".css": ("CSS", "#563d7c"),
    ".sh": ("Shell", "#89e051"),
    ".sql": ("SQL", "#e38c00"),
}

def get_public_commit_stats():
    lang_changes = defaultdict(int)
    lang_colors = {}

    # 1. Obter apenas repositórios públicos próprios (não forks)
    repos_url = f"https://api.github.com/users/{USERNAME}/repos?type=owner&per_page=100"
    repos = requests.get(repos_url, headers=HEADERS).json()

    for repo in repos:
        if repo.get("private") or repo.get("fork"):
            continue
        
        repo_name = repo["name"]
        # 2. Obter commits feitos por ti neste repositório público
        commits_url = f"https://api.github.com/repos/{USERNAME}/{repo_name}/commits?author={USERNAME}&per_page=100"
        commits = requests.get(commits_url, headers=HEADERS).json()

        if not isinstance(commits, list):
            continue

        for commit in commits[:30]: # Limite de 30 commits recentes por repo para rapidez
            sha = commit["sha"]
            detail_url = f"https://api.github.com/repos/{USERNAME}/{repo_name}/commits/{sha}"
            detail = requests.get(detail_url, headers=HEADERS).json()

            for file in detail.get("files", []):
                filename = file.get("filename", "")
                _, ext = os.path.splitext(filename.lower())
                if ext in EXT_MAP:
                    lang, color = EXT_MAP[ext]
                    # Contabiliza linhas adicionadas + modificadas no commit
                    changes = file.get("additions", 0) + file.get("changes", 0)
                    if changes > 0:
                        lang_changes[lang] += changes
                        lang_colors[lang] = color

    total = sum(lang_changes.values())
    if total == 0:
        return []

    sorted_langs = sorted(lang_changes.items(), key=lambda x: x[1], reverse=True)[:6]
    return [
        (lang, (count / total) * 100, lang_colors[lang])
        for lang, count in sorted_langs
    ]

def generate_svg(stats, filename, dark=True):
    bg_color = "#0d1117" if dark else "#ffffff"
    border_color = "#30363d" if dark else "#d0d7de"
    title_color = "#e6edf3" if dark else "#1f2328"
    text_color = "#8b949e" if dark else "#656d76"

    width = 540
    height = 175
    bar_width = 480
    bar_x = 30
    bar_y = 58

    # Construir segmentos da barra horizontal
    bar_segments = ""
    current_x = bar_x
    for i, (lang, pct, color) in enumerate(stats):
        seg_w = (pct / 100) * bar_width
        bar_segments += f'<rect x="{current_x:.2f}" y="{bar_y}" width="{seg_w:.2f}" height="8" fill="{color}" />\n'
        current_x += seg_w

    # Construir legenda em 2 colunas
    legend_items = ""
    for idx, (lang, pct, color) in enumerate(stats):
        col = idx % 2
        row = idx // 2
        x = 30 + (col * 250)
        y = 95 + (row * 26)
        legend_items += f'''
        <circle cx="{x + 5}" cy="{y - 4}" r="4.5" fill="{color}" />
        <text x="{x + 18}" y="{y}" fill="{title_color}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="13" font-weight="500">{lang}</text>
        <text x="{x + 115}" y="{y}" fill="{text_color}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="13">{pct:.1f}%</text>
        '''

    svg_content = f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="6" fill="{bg_color}" stroke="{border_color}"/>
      <text x="30" y="36" fill="{title_color}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="14" font-weight="600">Languages by Public Commits</text>
      
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

if __name__ == "__main__":
    stats = get_public_commit_stats()
    if stats:
        generate_svg(stats, "langs-dark.svg", dark=True)
        generate_svg(stats, "langs-light.svg", dark=False)
