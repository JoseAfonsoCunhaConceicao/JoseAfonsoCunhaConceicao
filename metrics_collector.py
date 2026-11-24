"""Data collection and aggregation engine for language metrics."""

import json
import os
import urllib.error
import urllib.request
from collections import defaultdict

USERNAME = "JoseAfonsoCunhaConceicao"
MAX_REPOS = 100
MAX_COMMITS_PER_REPO = 100
MAX_SEARCH_PAGES = 3
MAX_COMMITS_PER_PAGE = 30
REQUEST_TIMEOUT_SECONDS = 15

EXT_MAP = {
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".java": "Java",
    ".pl": "Prolog",
    ".pro": "Prolog",
    ".c": "C",
    ".h": "C",
    ".cpp": "C++",
    ".hpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".py": "Python",
    ".ipynb": "Python",
    ".s": "Assembly",
    ".asm": "Assembly",
    ".rs": "Rust",
    ".css": "CSS",
    ".scss": "CSS",
    ".html": "HTML",
    ".htm": "HTML",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".go": "Go",
    ".cs": "C#",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".swift": "Swift",
    ".sql": "SQL",
    ".r": "R",
    ".dart": "Dart",
    ".scala": "Scala",
    ".php": "PHP",
    ".rb": "Ruby",
}

IGNORED_PATHS = (
    "node_modules/", "target/", "dist/", "build/", "vendor/",
    ".next/", "out/", "coverage/", "__pycache__/", "bin/", "obj/",
    ".git/", "debug/", "release/"
)

IGNORED_EXTENSIONS = (
    ".min.js", ".min.css", ".lock", "-lock.json", ".o", ".out",
    ".class", ".pyc", ".png", ".jpg", ".jpeg", ".svg", ".gif",
    ".pdf", ".zip", ".tar", ".gz"
)

IGNORED_LANGUAGES = {"Rich Text Format"}


def is_valid_source_file(filepath: str) -> bool:
    """Validate if file is actual source code and not generated artifact."""
    assert isinstance(filepath, str), "filepath must be string"
    assert len(filepath) > 0, "filepath cannot be empty"

    path_lower = filepath.lower()
    for idx, ignored in enumerate(IGNORED_PATHS):
        if idx >= 20:
            break
        if ignored in path_lower:
            return False

    for idx, ext in enumerate(IGNORED_EXTENSIONS):
        if idx >= 20:
            break
        if path_lower.endswith(ext):
            return False

    return True


def fetch_api_json(url: str, token: str | None, extra_headers: dict | None = None) -> dict | list | None:
    """Safely fetch JSON from GitHub API with authentication and timeout."""
    assert isinstance(url, str), "URL must be string"
    assert url.startswith("https://api.github.com/"), "Invalid API URL"

    headers = {
        "User-Agent": "Metrics-Bot",
        "Accept": "application/vnd.github.v3+json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if extra_headers:
        for k, v in extra_headers.items():
            headers[k] = v

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
            data = resp.read().decode("utf-8")
            result = json.loads(data)
            assert result is not None, "Parsed result must not be None"
            return result
    except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError, OSError):
        return None


def fetch_repositories(token: str | None) -> list:
    """Fetch repositories accessible to the user with private fallback."""
    assert token is None or isinstance(token, str), "Token must be string or None"

    if token:
        user_url = (
            "https://api.github.com/user/repos"
            "?per_page=100&affiliation=owner,collaborator&visibility=all"
        )
        data = fetch_api_json(user_url, token)
        if isinstance(data, list) and len(data) > 0:
            assert len(data) <= MAX_REPOS, "Repos bound violated"
            return data

    public_url = f"https://api.github.com/users/{USERNAME}/repos?per_page=100&type=all"
    fallback = fetch_api_json(public_url, token)
    if isinstance(fallback, list):
        assert len(fallback) <= MAX_REPOS, "Fallback repos bound violated"
        return fallback
    return []


def collect_repo_commits(full_name: str, token: str | None) -> set[str]:
    """Retrieve user commit SHAs in repository to avoid duplicate counts."""
    assert isinstance(full_name, str) and "/" in full_name, "Invalid repo name"
    assert token is None or isinstance(token, str), "Invalid token"

    url = f"https://api.github.com/repos/{full_name}/commits?author={USERNAME}&per_page=100"
    commits_data = fetch_api_json(url, token)
    if not isinstance(commits_data, list):
        return set()

    shas = set()
    for idx, c in enumerate(commits_data):
        if idx >= MAX_COMMITS_PER_REPO:
            break
        if isinstance(c, dict) and "sha" in c:
            shas.add(c["sha"])
    return shas


def process_commit_files(commit_url: str, token: str | None, totals: defaultdict) -> None:
    """Inspect changed files in an external commit and aggregate additions."""
    assert isinstance(commit_url, str) and commit_url.startswith("https://api.github.com/"), "Invalid commit URL"
    assert isinstance(totals, defaultdict), "totals must be defaultdict"

    detail = fetch_api_json(commit_url, token)
    if not isinstance(detail, dict):
        return

    files = detail.get("files", [])
    if not isinstance(files, list):
        return

    for idx, f in enumerate(files):
        if idx >= 50:
            break
        filename = f.get("filename", "")
        if not is_valid_source_file(filename):
            continue
        _, ext = os.path.splitext(filename.lower())
        lang = EXT_MAP.get(ext)
        if not lang:
            continue
        additions = f.get("additions", 0)
        if additions > 0:
            totals[lang] += additions * 25


def process_external_commits(
    token: str | None, owned_repos: set[str], seen_shas: set[str], totals: defaultdict
) -> None:
    """Tally user commits in external repositories with deduplication."""
    assert isinstance(owned_repos, set), "owned_repos must be a set"
    assert isinstance(seen_shas, set), "seen_shas must be a set"

    search_headers = {"Accept": "application/vnd.github.cloak-preview+json"}
    for page in range(1, MAX_SEARCH_PAGES + 1):
        url = (
            f"https://api.github.com/search/commits?q=author:{USERNAME}"
            f"&sort=author-date&order=desc&per_page={MAX_COMMITS_PER_PAGE}&page={page}"
        )
        res = fetch_api_json(url, token, search_headers)
        if not isinstance(res, dict):
            break
        items = res.get("items", [])
        if not isinstance(items, list) or len(items) == 0:
            break
        for idx, item in enumerate(items):
            if idx >= MAX_COMMITS_PER_PAGE:
                break
            sha = item.get("sha")
            if not sha or sha in seen_shas:
                continue
            seen_shas.add(sha)
            repo_info = item.get("repository", {})
            full_name = repo_info.get("full_name")
            if full_name in owned_repos:
                continue
            commit_url = item.get("url")
            if isinstance(commit_url, str):
                process_commit_files(commit_url, token, totals)


def process_owned_repositories(
    repos: list, token: str | None, owned_repos: set[str], seen_shas: set[str]
) -> defaultdict:
    """Tally languages from owned repos and record commit SHAs."""
    assert isinstance(repos, list), "repos must be a list"
    assert isinstance(owned_repos, set), "owned_repos must be a set"

    totals = defaultdict(int)
    for idx, repo in enumerate(repos):
        if idx >= MAX_REPOS:
            break
        if not isinstance(repo, dict):
            continue
        full_name = repo.get("full_name")
        if not isinstance(full_name, str):
            continue
        owned_repos.add(full_name)
        repo_shas = collect_repo_commits(full_name, token)
        seen_shas.update(repo_shas)

        if repo.get("fork"):
            continue

        url = f"https://api.github.com/repos/{full_name}/languages"
        lang_data = fetch_api_json(url, token)
        if isinstance(lang_data, dict):
            for l_idx, (lang, count) in enumerate(lang_data.items()):
                if l_idx >= 50:
                    break
                if isinstance(count, int) and lang not in IGNORED_LANGUAGES:
                    totals[lang] += count
    return totals


def collect_all_language_stats(token: str | None) -> list[tuple[str, float]]:
    """Execute end-to-end collection across owned and external repositories."""
    assert USERNAME is not None and len(USERNAME) > 0, "USERNAME required"

    repos = fetch_repositories(token)
    assert isinstance(repos, list), "repos must be a list"

    owned_repos = set()
    seen_shas = set()

    totals = process_owned_repositories(repos, token, owned_repos, seen_shas)
    process_external_commits(token, owned_repos, seen_shas, totals)

    total_bytes = sum(totals.values())
    if total_bytes == 0:
        return []

    sorted_langs = sorted(totals.items(), key=lambda x: x[1], reverse=True)
    results = []
    for idx, (lang, bytes_count) in enumerate(sorted_langs):
        if idx >= 50:
            break
        pct = (bytes_count / total_bytes) * 100.0
        results.append((lang, pct))
    return results
