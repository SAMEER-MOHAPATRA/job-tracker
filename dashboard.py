"""
dashboard.py — generates a local HTML dashboard from the store.

Usage:
    python dashboard.py
    python dashboard.py --open   # auto-open in browser
"""

import argparse
import webbrowser
from collections import Counter
from datetime import datetime, timezone
from html import escape
from pathlib import Path

import store

DASHBOARD_PATH = Path("dashboard.html")

# ---- points system (from resume: DA/AE profile, remote-first) ----
# title: Data Analyst ranks highest, other target roles below
TITLE_POINTS = [
    ("data analyst", 30),
    ("business analyst", 20),
    ("analytics engineer", 20),
]
# location: remote first, then India
LOCATION_POINTS = [
    ("remote", 20), ("work from anywhere", 20), ("anywhere", 20),
    ("india", 10),
]
# skills pulled from resume — +5 each, found in title or summary
SKILL_KEYWORDS = [
    "sql", "python", "power bi", "tableau", "excel",
    "etl", "dax", "power query", "pandas",
]
SKILL_POINT, SKILL_CAP = 5, 25


def score_job(job: dict) -> int:
    title = job.get("title", "").lower()
    haystack = title + " " + job.get("summary", "").lower() + " " + job.get("location", "").lower()
    pts = 0
    for kw, p in TITLE_POINTS:
        if kw in title:
            pts += p
            break
    for kw, p in LOCATION_POINTS:
        if kw in haystack:
            pts += p
            break
    pts += min(SKILL_CAP, sum(SKILL_POINT for kw in SKILL_KEYWORDS if kw in haystack))
    # freshness dominates: apply fast while postings are new
    age = datetime.now(timezone.utc) - store._parse(job.get("published", ""), store.UTC_FMT)
    if age.days <= 1:
        pts += 50
    elif age.days <= 3:
        pts += 40
    elif age.days <= 7:
        pts += 25
    elif age.days <= 14:
        pts += 10
    return pts


def _build_html(
    total_jobs: int,
    jobs_week: int,
    feed_breakdown: list[tuple[str, int]],
    ranked_jobs: list[dict],
    total_apps: int,
    apps_week: int,
) -> str:
    # escape at the render boundary — feed data is untrusted
    feed_rows = "".join(
        f"<tr><td>{escape(label)}</td>"
        f"<td class='num'>{count}</td></tr>"
        for label, count in feed_breakdown
    )
    job_rows = []
    for j in ranked_jobs:
        applied = j.get("applied", "").strip().lower() in ("yes", "true", "1") or j.get("applied", "").strip()
        link = j.get("link", "")
        apply_cell = (
            "<span class='muted'>Applied</span>" if applied
            else f"<a class='apply' href='{escape(link)}' data-id='{escape(j.get('id', ''))}' "
                 f"data-title='{escape(j['title'])}' target='_blank'>Apply</a>" if link
            else "<span class='muted'>—</span>"
        )
        job_rows.append(
            f"<tr{' class=done' if applied else ''}>"
            f"<td class='num'>{j['_score']}</td>"
            f"<td>{escape(j['title'])}</td>"
            f"<td>{escape(j.get('source', ''))}</td>"
            f"<td class='muted'>{escape(j.get('published', ''))}</td>"
            f"<td>{apply_cell}</td></tr>"
        )
    job_rows = "".join(job_rows)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Job Tracker Dashboard</title>
<style>
/* coffee palette: espresso text, mocha accent, caramel highlight, latte muted, cream bg */
:root {{
  --espresso: #3b2a20;
  --mocha: #6f4e37;
  --caramel: #b57b3f;
  --latte: #9c8672;
  --cream: #f6f0e7;
  --card: #fffbf4;
  --line: #e7dccb;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0 auto; padding: 2.5rem 1.5rem; max-width: 64rem;
  background: var(--cream); color: var(--espresso);
  font: 15px/1.5 -apple-system, "Segoe UI", system-ui, sans-serif;
}}
h1 {{ margin: 0 0 .25rem; font-size: 1.6rem; font-weight: 600; color: var(--mocha); }}
h2 {{ margin: 0 0 .75rem; font-size: 1.05rem; font-weight: 600; color: var(--mocha); }}
.muted {{ color: var(--latte); font-size: .85rem; }}
.stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1rem; margin: 1.75rem 0; }}
.card {{
  background: var(--card); border: 1px solid var(--line);
  border-radius: .75rem; padding: 1rem 1.25rem;
}}
.stat-label {{ margin: 0; font-size: .8rem; color: var(--latte); }}
.stat-value {{ margin: .2rem 0 0; font-size: 2rem; font-weight: 700; color: var(--mocha); }}
.stat-value.accent {{ color: var(--caramel); }}
.panels {{ display: grid; grid-template-columns: 1fr; gap: 1.25rem; }}
@media (min-width: 768px) {{ .panels {{ grid-template-columns: 1fr 1fr; }} }}
table {{ width: 100%; border-collapse: collapse; font-size: .875rem; }}
th, td {{ padding: .5rem .6rem; text-align: left; border-bottom: 1px solid var(--line); }}
th {{ color: var(--latte); font-weight: 500; }}
tr:last-child td {{ border-bottom: none; }}
td.num, th.num {{ text-align: right; color: var(--caramel); font-weight: 600; }}
a.apply {{
  display: inline-block; padding: .2rem .7rem; border-radius: .5rem;
  background: var(--mocha); color: var(--cream); text-decoration: none;
  font-size: .8rem; font-weight: 600;
}}
a.apply:hover {{ background: var(--caramel); }}
tr.done td {{ opacity: .45; }}
</style>
</head>
<body>
<h1>Job Tracker Dashboard</h1>
<p class="muted">Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>

<div class="stats">
  <div class="card">
    <p class="stat-label">Total Jobs</p>
    <p class="stat-value">{total_jobs}</p>
  </div>
  <div class="card">
    <p class="stat-label">Jobs This Week</p>
    <p class="stat-value accent">{jobs_week}</p>
  </div>
  <div class="card">
    <p class="stat-label">Applications</p>
    <p class="stat-value">{total_apps}</p>
  </div>
  <div class="card">
    <p class="stat-label">Applied This Week</p>
    <p class="stat-value accent">{apps_week}</p>
  </div>
</div>

<div class="panels">
  <div class="card">
    <h2>Jobs by Feed</h2>
    <table>
      <thead><tr><th>Feed</th><th class="num">Count</th></tr></thead>
      <tbody>{feed_rows}</tbody>
    </table>
  </div>
</div>

<div class="card" style="margin-top:1.25rem">
  <h2>All Jobs — Ranked</h2>
  <p class="muted" style="margin:0 0 .75rem">Points: freshness (≤1d 50 / ≤3d 40 / ≤7d 25 / ≤14d 10) + title match (DA 30 / BA·AE 20) + remote 20 / India 10 + resume skills (5 each, max 25)</p>
  <table>
    <thead><tr><th class="num">Score</th><th>Title</th><th>Source</th><th>Published</th><th>Apply</th></tr></thead>
    <tbody>{job_rows}</tbody>
  </table>
</div>
<script>
// remember which Apply links were clicked; ask about them on revisit
const KEY = 'pendingApply';
const load = () => JSON.parse(localStorage.getItem(KEY) || '{{}}');
const save = p => localStorage.setItem(KEY, JSON.stringify(p));

document.querySelectorAll('a.apply').forEach(a =>
  a.addEventListener('click', () => {{
    const p = load();
    p[a.dataset.id] = a.dataset.title;
    save(p);
  }})
);

let asking = false;
async function askPending() {{
  if (asking) return;
  asking = true;
  const p = load();
  for (const [id, title] of Object.entries(p)) {{
    const yes = confirm('Did you apply to:\\n\\n' + title + '?');
    delete p[id];
    save(p);
    if (yes) {{
      await fetch('/applied/' + encodeURIComponent(id), {{method: 'POST'}});
      location.reload();
      return;
    }}
  }}
  asking = false;
}}

window.addEventListener('load', askPending);
document.addEventListener('visibilitychange', () => {{
  if (!document.hidden) askPending();
}});
</script>
</body>
</html>"""


def main(open_browser: bool = False) -> None:
    jobs = store.load_jobs()
    apps = store.load_applications()

    jobs_week = store.this_week(jobs, "published", store.UTC_FMT)
    apps_week = store.this_week(apps, "date_applied")

    feed_breakdown = Counter(j.get("source", "Unknown") for j in jobs).most_common()

    for j in jobs:
        j["_score"] = score_job(j)
    # newest first, then stable-sort by score so ties stay newest-first
    jobs.sort(key=lambda j: j.get("published", ""), reverse=True)
    ranked = sorted(jobs, key=lambda j: -j["_score"])

    html = _build_html(
        total_jobs=len(jobs),
        jobs_week=len(jobs_week),
        feed_breakdown=feed_breakdown,
        ranked_jobs=ranked,
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
