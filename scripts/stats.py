#!/usr/bin/env python3
"""Refresh the stats block in README.md from public GitHub data.

Reads GH_TOKEN and GH_USER from the environment. Any section whose API call
fails is rendered as "n/a" so the daily job never fails because of stats.
"""
import datetime as dt
import json
import os
import re
import sys
import urllib.request
from collections import Counter

API = "https://api.github.com"
START, END = "<!-- stats:start -->", "<!-- stats:end -->"


def request(url, body=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None)
    req.add_header("Authorization", f"Bearer {os.environ['GH_TOKEN']}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "daily-stats")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def repo_stats(user):
    repos, page = [], 1
    while True:
        batch = request(f"{API}/users/{user}/repos?type=owner&per_page=100&page={page}")
        repos += batch
        if len(batch) < 100:
            break
        page += 1
    own = [r for r in repos if not r["fork"]]
    langs = Counter(r["language"] for r in own if r["language"])
    stars = sum(r["stargazers_count"] for r in own)
    return len(own), stars, ", ".join(f"{name} ({n})" for name, n in langs.most_common(5))


def calendar_stats(user, today):
    query = """query($login:String!){ user(login:$login){ contributionsCollection{
      contributionCalendar{ totalContributions weeks{ contributionDays{ date contributionCount }}}}}}"""
    data = request(f"{API}/graphql", {"query": query, "variables": {"login": user}})
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = {d["date"]: d["contributionCount"] for w in cal["weeks"] for d in w["contributionDays"]}
    day = today
    if days.get(day.isoformat(), 0) == 0:  # today's own commit isn't pushed yet
        day -= dt.timedelta(days=1)
    streak = 0
    while days.get(day.isoformat(), 0) > 0:
        streak += 1
        day -= dt.timedelta(days=1)
    return cal["totalContributions"], streak


def safe(fn, *args, fallback):
    try:
        return fn(*args)
    except Exception as exc:  # stats are best-effort
        print(f"warning: {fn.__name__} failed: {exc}", file=sys.stderr)
        return fallback


def main():
    user = os.environ["GH_USER"]
    today = dt.datetime.now(dt.timezone.utc).date()
    repos, stars, langs = safe(repo_stats, user, fallback=("n/a", "n/a", "n/a"))
    total, streak = safe(calendar_stats, user, today, fallback=("n/a", "n/a"))

    block = "\n".join([
        START,
        f"_Updated {today.isoformat()} (UTC)._",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Contributions, last 12 months | {total} |",
        f"| Current streak (days) | {streak} |",
        f"| Public repos (not forks) | {repos} |",
        f"| Stars on public repos | {stars} |",
        f"| Top languages (by repo count) | {langs or 'n/a'} |",
        END,
    ])

    path = "README.md"
    text = open(path, encoding="utf-8").read()
    pattern = re.compile(re.escape(START) + ".*?" + re.escape(END), re.S)
    if not pattern.search(text):
        sys.exit("README.md has no stats markers")
    open(path, "w", encoding="utf-8").write(pattern.sub(lambda _: block, text))


if __name__ == "__main__":
    main()
