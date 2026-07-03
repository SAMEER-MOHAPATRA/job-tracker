"""
dashboard.py — generates a local HTML dashboard from the store.

Usage:
    python dashboard.py
    python dashboard.py --open   # auto-open in browser
"""

import argparse
import webbrowser
from collections import Counter
from datetime import datetime
from html import escape
from pathlib import Path

import store

DASHBOARD_PATH = Path("dashboard.html")


def _build_html(
    total_jobs: int,
    jobs_week: int,
    feed_breakdown: list[tuple[str, int]],
    recent_jobs: list[dict],
    total_apps: int,
    apps_week: int,
) -> str:
    # escape at the render boundary — feed data is untrusted
    feed_rows = "".join(
        f"<tr><td class='px-4 py-2'>{escape(label)}</td>"
        f"<td class='px-4 py-2 text-right'>{count}</td></tr>"
        for label, count in feed_breakdown
    )
    job_rows = "".join(
        f"<tr><td class='px-4 py-2'>{escape(j['title'])}</td>"
        f"<td class='px-4 py-2'>{escape(j.get('company', ''))}</td>"
        f"<td class='px-4 py-2'>{escape(j.get('source', ''))}</td>"
        f"<td class='px-4 py-2 text-sm text-slate-500'>{escape(j.get('published', ''))}</td></tr>"
        for j in recent_jobs
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Job Tracker Dashboard</title>
<script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-50 p-6 max-w-5xl mx-auto">
<h1 class="text-3xl font-bold text-slate-800 mb-6">Job Tracker Dashboard</h1>
<p class="text-slate-500 mb-6">Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>

<div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
  <div class="bg-white rounded-xl shadow p-4">
    <p class="text-sm text-slate-500">Total Jobs</p>
    <p class="text-3xl font-bold text-indigo-600">{total_jobs}</p>
  </div>
  <div class="bg-white rounded-xl shadow p-4">
    <p class="text-sm text-slate-500">Jobs This Week</p>
    <p class="text-3xl font-bold text-emerald-600">{jobs_week}</p>
  </div>
  <div class="bg-white rounded-xl shadow p-4">
    <p class="text-sm text-slate-500">Applications</p>
    <p class="text-3xl font-bold text-indigo-600">{total_apps}</p>
  </div>
  <div class="bg-white rounded-xl shadow p-4">
    <p class="text-sm text-slate-500">Applied This Week</p>
    <p class="text-3xl font-bold text-emerald-600">{apps_week}</p>
  </div>
</div>

<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
  <div class="bg-white rounded-xl shadow p-4">
    <h2 class="text-lg font-semibold text-slate-700 mb-3">Jobs by Feed</h2>
    <table class="w-full text-sm">
      <thead><tr class="border-b text-slate-500"><th class="text-left px-4 py-2">Feed</th><th class="text-right px-4 py-2">Count</th></tr></thead>
      <tbody>{feed_rows}</tbody>
    </table>
  </div>
  <div class="bg-white rounded-xl shadow p-4">
    <h2 class="text-lg font-semibold text-slate-700 mb-3">Recent Jobs</h2>
    <table class="w-full text-sm">
      <thead><tr class="border-b text-slate-500"><th class="text-left px-4 py-2">Title</th><th class="text-left px-4 py-2">Company</th><th class="text-left px-4 py-2">Source</th><th class="text-left px-4 py-2">Published</th></tr></thead>
      <tbody>{job_rows}</tbody>
    </table>
  </div>
</div>
</body>
</html>"""


def main(open_browser: bool = False) -> None:
    jobs = store.load_jobs()
    apps = store.load_applications()

    jobs_week = store.this_week(jobs, "published", store.UTC_FMT)
    apps_week = store.this_week(apps, "date_applied")

    feed_breakdown = Counter(j.get("source", "Unknown") for j in jobs).most_common()

    recent = sorted(jobs, key=lambda j: j.get("published", ""), reverse=True)[:20]

    html = _build_html(
        total_jobs=len(jobs),
        jobs_week=len(jobs_week),
        feed_breakdown=feed_breakdown,
        recent_jobs=recent,
        total_apps=len(apps),
        apps_week=len(apps_week),
    )

    DASHBOARD_PATH.write_text(html, encoding="utf-8")
    print(f"[OK] Dashboard written to {DASHBOARD_PATH}")

    if open_browser:
        webbrowser.open(DASHBOARD_PATH.resolve().as_uri())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate job tracker dashboard")
    parser.add_argument("--open", action="store_true", help="Open dashboard in browser")
    args = parser.parse_args()
    main(open_browser=args.open)
