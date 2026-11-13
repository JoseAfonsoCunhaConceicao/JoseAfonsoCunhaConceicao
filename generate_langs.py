import os
import time
import requests
from collections import defaultdict

USERNAME = "JoseAfonsoCunhaConceicao"
TOKEN = os.environ.get("GITHUB_TOKEN")
HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
} if TOKEN else {"Accept": "application/vnd.github.v3+json"}

# Cores oficiais do GitHub
LANG_COLORS = {
    "Rust": "#dea584",
    "C": "#555555",
    "C++": "#f34b7d",
    "Python": "#3572A5",
    "TypeScript": "#3178c6",
    "JavaScript": "#f1e05a",
    "Java": "#b07219",
    "Go": "#00ADD8",
    "C#": "#178600",
    "Assembly": "#6E4C13",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Shell": "#89e051",
    "SQL": "#e38c00",
    "Makefile": "#427819",
}

EXT_MAP = {
    ".rs": "Rust",
    ".c": "C", ".h": "C",
    ".cpp": "C++", ".hpp": "C++", ".cc": "C++",
    ".py": "Python",
    ".ts": "TypeScript", ".tsx": "TypeScript",
    ".js": "JavaScript", ".jsx": "JavaScript",
    ".java": "Java",
    ".go": "Go",
    ".cs": "C#",
    ".asm": "Assembly", ".s": "Assembly",
    ".html": "HTML",
    ".css": "CSS",
    ".sh": "Shell",
    ".sql": "SQL",
}

IGNORED_PATHS = (
    "node_modules/", "target/", "dist/", "build/", "vendor/",
    ".next/", "out/", "coverage/", "__pycache__/"
)

def is_valid_file(filepath):
    path_lower = filepath.lower()
    if any(ignored in path_lower for ignored in IGNORED_PATHS):
        return False
    if path_lower.endswith((".min.js", ".min.css", ".lock", "-lock.json")):
        return False
    return True

def get_combined_stats():
    lang_bytes = defaultdict(int)
    owned_repos = set()

    # 1. Tudo o que está nos teus repositórios públicos próprios (já ignora vendored/node_modules)
    repos_url = f"https://api.github.com/users/{USERNAME}/repos?type=owner&per_page=100"
    repos = requests.get(repos_url, headers=HEADERS).json()

    if isinstance(repos, list):
        for repo in repos:
            if repo.get("private"):
                continue
            full_name = repo["full_name"]
            owned_repos.add(full_name)

            # Se for fork, não conta o código base do fork (só os teus commits no passo 2)
            if repo.get("fork"):
                continue

            langs_url = repo["languages_url"]
            repo_langs = requests.get(langs_url, headers=HEADERS).json()
            if isinstance(repo_langs, dict):
                for lang, bytes_count in repo_langs.items():
                    if lang in LANG_COLORS:
                        lang_bytes[lang] += bytes_count

    # 2. Todos os commits públicos feitos por ti em repositórios que NÃO são teus (orgs, forks, terceiros)
    search_headers = HEADERS.copy()
    search_headers["Accept"] = "application/vnd.github.cloak-preview+json"

    for page in range(1, 4): # Até 300 commits externos mais recentes
        search_url = f"https://api.github.com/search/commits?q=author:{USERNAME}&sort=author-date&order=desc&per_page=100&page={page}"
        res = requests.get(search_url, headers=search_headers).json()
        items = res.get("items", [])
        if not items:
            break

        for item in items:
            repo_info = item.get("repository", {})
            # Ignora repositórios privados e repositórios próprios (já contados no passo 1)
            if repo_info.get("private", True):
                continue
            repo_full_name = repo_info.get("full_name")
            if repo_full_name in owned_repos and not repo_info.get("fork"):
                continue

            commit_url = item.get("url")
            detail = requests.get(commit_url, headers=HEADERS).json()
            for file in detail.get("files", []):
                filename = file.get("filename", "")
                if not is_valid_file(filename):
                    continue
                _, ext = os.path.splitext(filename.lower())
                if ext in EXT_MAP:
                    lang = EXT_MAP[ext]
                    # Estima peso em bytes (~40 bytes por linha alterada) para equilibrar com a métrica do passo 1
                    lines = file.get("additions", 0) + file.get("changes", 0)
                    if lines > 0:
                        lang_bytes[lang] += lines * 40

        time.sleep(1) # Evita rate-limit da API de pesquisa

    total = sum(lang_bytes.values())
    if total == 0:
        return []

    sorted_langs = sorted(lang_bytes.items(), key=lambda x: x[1], reverse=True)[:6]
    return [
        (lang, (count / total) * 100, LANG_COLORS.get(lang, "#8b949e"))
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
        y = 95 + (row * 26)
        legend_items += f'''
        <circle cx="{x + 5}" cy="{y - 4}" r="4.5" fill="{color}" />
        <text x="{x + 18}" y="{y}" fill="{title_color}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="13" font-weight="500">{lang}</text>
        <text x="{x + 115}" y="{y}" fill="{text_color}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="13">{pct:.1f}%</text>
        '''

    svg_content = f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="6" fill="{bg_color}" stroke="{border_color}"/>
      <text x="30" y="36" fill="{title_color}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="14" font-weight="600">Most Used Languages</text>
      
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
    stats = get_combined_stats()
    if stats:
        generate_svg(stats, "langs-dark.svg", dark=True)
        generate_svg(stats, "langs-light.svg", dark=False)
