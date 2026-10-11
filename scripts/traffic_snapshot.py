#!/usr/bin/env python3
"""Append a daily snapshot of repo traffic + counters to metrics/traffic.csv.

Why this exists: GitHub's traffic API only ever returns a rolling 14-day
window. If you don't record it, the history is gone. This is the only way
to know how many people actually cloned / viewed over time.

Usage:
    # locally, using the gh CLI for auth
    python3 scripts/traffic_snapshot.py

    # in Actions, using an env token
    GITHUB_TOKEN=... GITHUB_REPOSITORY=owner/repo python3 scripts/traffic_snapshot.py

Writes (and is idempotent per day — re-running the same day overwrites that
day's row rather than duplicating it):

    metrics/traffic.csv
"""

from __future__ import annotations

import csv
import json
import os
import pathlib
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "metrics" / "traffic.csv"

FIELDS = [
    "date",
    "stars",
    "forks",
    "watchers",
    "views_total",
    "views_unique",
    "clones_total",
    "clones_unique",
    "release_downloads",
    "referrers",
]


def gh_api(path: str) -> dict | list:
    """GET an api.github.com path. Uses GITHUB_TOKEN if set, else the gh CLI."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    url = f"https://api.github.com{path}"

    if token:
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "zack-design-skills-metrics",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")[:300]
            raise SystemExit(
                f"GitHub API {exc.code} on {path}: {body}\n"
                "The traffic endpoints need push access. In Actions, add a "
                "PAT with `repo` scope as the TRAFFIC_TOKEN secret and pass it "
                "as GITHUB_TOKEN for this step."
            ) from exc

    try:
        raw = subprocess.run(
            ["gh", "api", path], capture_output=True, text=True, check=True
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise SystemExit(f"no GITHUB_TOKEN and gh CLI failed on {path}: {exc}") from exc
    return json.loads(raw)


def main() -> int:
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        try:
            repo = subprocess.run(
                ["gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"],
                capture_output=True, text=True, check=True,
            ).stdout.strip()
        except Exception:
            raise SystemExit("set GITHUB_REPOSITORY=owner/repo (or run inside the git repo with gh available)")

    info = gh_api(f"/repos/{repo}")
    clones = gh_api(f"/repos/{repo}/traffic/clones")
    views = gh_api(f"/repos/{repo}/traffic/views")
    try:
        referrers = gh_api(f"/repos/{repo}/traffic/popular/referrers")
    except SystemExit:
        referrers = []

    releases = gh_api(f"/repos/{repo}/releases")
    downloads = sum(
        asset.get("download_count", 0)
        for rel in releases
        for asset in rel.get("assets", [])
    )

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    row = {
        "date": today,
        "stars": info.get("stargazers_count", 0),
        "forks": info.get("forks_count", 0),
        "watchers": info.get("subscribers_count", 0),
        "views_total": views.get("count", 0),
        "views_unique": views.get("uniques", 0),
        "clones_total": clones.get("count", 0),
        "clones_unique": clones.get("uniques", 0),
        "release_downloads": downloads,
        "referrers": "; ".join(
            f"{r.get('referrer')}({r.get('count')})" for r in referrers[:5]
        ),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    existing: list[dict] = []
    if OUT.is_file():
        with OUT.open(newline="", encoding="utf-8") as fh:
            existing = [r for r in csv.DictReader(fh) if r.get("date") != today]
    existing.append(row)
    existing.sort(key=lambda r: r["date"])

    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(existing)

    print(f"{today}  stars={row['stars']} forks={row['forks']} "
          f"clones={row['clones_total']} ({row['clones_unique']} unique) "
          f"views={row['views_total']} ({row['views_unique']} unique) "
          f"downloads={downloads}")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(existing)} days recorded)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
