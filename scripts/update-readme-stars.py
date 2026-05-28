#!/usr/bin/env python3
"""Update star counts in profile README list items linked to GitHub repos."""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request

OWNER = "AlexeyPerov"
README_PATH = "README.md"
LINE_RE = re.compile(
    rf"^(- \[\*\*(?P<title>[^*]+)\*\*\]\(https://github\.com/{re.escape(OWNER)}/(?P<repo>[^)]+)\))"
    r"\s*(?:·\s*(?:⭐\s*\d+\s*)?)?—(?P<desc>.*)$"
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


def format_line(title: str, repo: str, desc: str, stars: int | None) -> str:
    prefix = f"- [**{title}**](https://github.com/{OWNER}/{repo})"
    if stars is not None and stars > 0:
        return f"{prefix} · ⭐ {stars} —{desc}"
    return f"{prefix} —{desc}"


def main() -> int:
    with open(README_PATH, encoding="utf-8") as handle:
        lines = handle.readlines()

    updated_lines: list[str] = []
    changed = False

    for line in lines:
        stripped = line.rstrip("\n")
        match = LINE_RE.match(stripped)
        if not match:
            updated_lines.append(line)
            continue

        title = match.group("title")
        repo = match.group("repo")
        desc = match.group("desc")
        stars = fetch_stars(repo)
        new_line = format_line(title, repo, desc, stars)

        if new_line != stripped:
            changed = True
            print(f"Updated {repo}: {stars or 0} stars")

        updated_lines.append(new_line + "\n")

    if changed:
        with open(README_PATH, "w", encoding="utf-8") as handle:
            handle.writelines(updated_lines)
        print("README.md updated")
        return 0

    print("No changes needed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
