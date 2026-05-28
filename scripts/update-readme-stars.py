#!/usr/bin/env python3
"""Update star counts in profile README for linked GitHub repos."""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request

OWNER = "AlexeyPerov"
README_PATH = "README.md"
LINK_RE = re.compile(
    rf'(<a href="https://github\.com/{re.escape(OWNER)}/(?P<repo>[^"]+)">[^<]+</a></strong>)'
    r"(?:\s*·\s*⭐\s*\d+)?"
)


def github_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "profile-readme-stars-updater",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def fetch_stars(repo: str) -> int | None:
    url = f"https://api.github.com/repos/{OWNER}/{repo}"
    request = urllib.request.Request(url, headers=github_headers())
    try:
        with urllib.request.urlopen(request) as response:
            data = json.load(response)
            return int(data["stargazers_count"])
    except urllib.error.HTTPError as error:
        if error.code == 404:
            print(f"Warning: repo not found: {repo}", file=sys.stderr)
            return None
        raise


def stars_suffix(stars: int | None) -> str:
    if stars is not None and stars > 0:
        return f" · ⭐ {stars}"
    return ""


def collect_repos(content: str) -> set[str]:
    return {match.group("repo") for match in LINK_RE.finditer(content)}


def update_content(content: str) -> tuple[str, bool]:
    star_cache = {repo: fetch_stars(repo) for repo in sorted(collect_repos(content))}
    changed = False

    def replacer(match: re.Match[str]) -> str:
        nonlocal changed
        repo = match.group("repo")
        replacement = match.group(1) + stars_suffix(star_cache.get(repo))
        if replacement != match.group(0):
            changed = True
            print(f"Updated {repo}: {star_cache.get(repo) or 0} stars")
        return replacement

    return LINK_RE.sub(replacer, content), changed


def main() -> int:
    with open(README_PATH, encoding="utf-8") as handle:
        content = handle.read()

    updated_content, changed = update_content(content)

    if changed:
        with open(README_PATH, "w", encoding="utf-8") as handle:
            handle.write(updated_content)
        print("README.md updated")
        return 0

    print("No changes needed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
