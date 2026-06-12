"""
job_discovery.py — scrapes DA/BA jobs from Indeed India, RemoteOK, We Work Remotely.
Appends new listings to jobs_found.csv; skips anything already seen.

Usage:
    python job_discovery.py
    python job_discovery.py --days 14
"""

import argparse
import csv
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode, urlparse

import feedparser

DEFAULT_DAYS = 7
MAX_PER_FEED = int(os.getenv("MAX_PER_FEED", "25"))

ROLE_KEYWORDS = [
    "data analyst", "business analyst", "data analytics",
    "analytics analyst", "reporting analyst", "bi analyst",
    "power bi", "sql analyst", "insights analyst",
]

SENIORITY_BLOCK = [
    "senior", "lead", "manager", "director", "sr.",
    "head of", "principal", "vp ", "vice president", "associate director",
]

# Higher score = better fit for JSPL/logistics background.
DOMAIN_SCORES = {
    "logistics": 3, "supply chain": 3, "railway": 3,
    "operations": 2, "manufacturing": 2, "steel": 2, "consulting": 2,
    "erp": 1, "sap": 1, "tableau": 1, "power bi": 1, "python": 1, "sql": 1,
}


def build_feeds(days: int) -> list[tuple[str, str]]:
    base = "https://rss.indeed.com/rss"

    def indeed(label: str, query: str, location: str) -> tuple[str, str]:
        params = urlencode({"q": query, "l": location, "fromage": min(days, 14), "sort": "date"})
        return label, f"{base}?{params}"

    return [
        indeed("Indeed | DA India",        "data analyst",        "India"),
        indeed("Indeed | BA India",         "business analyst",    "India"),
        indeed("Indeed | DA Bengaluru",     "data analyst",        "Bengaluru, Karnataka"),
        indeed("Indeed | DA Hyderabad",     "data analyst",        "Hyderabad, Telangana"),
        indeed("Indeed | DA Mumbai",        "data analyst",        "Mumbai, Maharashtra"),
        indeed("Indeed | DA Remote India",  "remote data analyst", "India"),
        ("RemoteOK | All Remote",     "https://remoteok.com/remote-jobs.rss"),
        ("WWR | Programming & Data",  "https://weworkremotely.com/categories/remote-programming-jobs.rss"),
        ("WWR | Business",            "https://weworkremotely.com/categories/remote-management-and-finance-jobs.rss"),
    ]


def load_seen_ids() -> set[str]:
    seen = set()
    for fname in ("jobs_applied.csv", "jobs_found.csv"):
        try:
            with open(fname, "r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    seen.update(filter(None, [row.get("id"), row.get("link")]))
        except FileNotFoundError:
            pass
    return seen


def parse_published(entry) -> datetime:
    for field in ("published_parsed", "updated_parsed", "created_parsed"):
        t = getattr(entry, field, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return datetime.now(timezone.utc)


def extract_job_id(url: str) -> str:
    tail = urlparse(url).path.rstrip("/").split("/")[-1]
    return re.sub(r"[^a-zA-Z0-9_\-]", "", tail) or url


def is_relevant(title: str, description: str) -> bool:
    combined = (title + " " + description).lower()
    if not any(kw in combined for kw in ROLE_KEYWORDS):
        return False
    if any(flag in title.lower() for flag in SENIORITY_BLOCK):
        return False
    return True


def calc_domain_score(title: str, description: str) -> int:
    text = (title + " " + description).lower()
    return sum(v for kw, v in DOMAIN_SCORES.items() if kw in text)


def process_feed(label: str, url: str, days: int, seen: set[str]) -> tuple[list[dict], str | None]:
    # Rocky note: one feed, one try. Either it works or it doesn't.
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    results = []
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:MAX_PER_FEED]:
            if parse_published(entry) < cutoff:
                continue
            job_id = extract_job_id(entry.link)
            if job_id in seen or entry.link in seen:
                continue
            title = getattr(entry, "title", "").strip()
            description = getattr(entry, "summary", "").strip()
            if not is_relevant(title, description):
                continue
            results.append({
                "id":           job_id,
                "title":        title,
                "company":      getattr(entry, "author", "Unknown"),
                "location":     getattr(entry, "location", "Not specified"),
                "source":       label,
                "link":         entry.link,
                "published":    parse_published(entry).strftime("%Y-%m-%d %H:%M UTC"),
                "domain_score": calc_domain_score(title, description),
                "applied":      "",
            })
            seen.update([job_id, entry.link])
    except Exception as exc:
        return results, str(exc)
    return results, None


def main(days: int) -> None:
    seen = load_seen_ids()
    all_jobs: list[dict] = []
    feed_stats: list[tuple] = []

    for label, url in build_feeds(days):
        jobs, error = process_feed(label, url, days, seen)
        all_jobs.extend(jobs)
        feed_stats.append((label, f"ERROR: {error}" if error else len(jobs), MAX_PER_FEED))

    all_jobs.sort(key=lambda x: (x["domain_score"], x["published"]), reverse=True)

    if all_jobs:
        out = Path("jobs_found.csv")
        write_header = not out.exists()
        with open(out, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=all_jobs[0].keys())
            if write_header:
                writer.writeheader()
            writer.writerows(all_jobs)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"\n[{ts}]  Job Discovery  |  window: last {days} days")
    print("-" * 55)
    for label, found, total in feed_stats:
        print(f"  {label:<35} {str(found):>4} new / {total} scanned")
    print("-" * 55)
    if all_jobs:
        top = all_jobs[0]
        print(f"  ✅ {len(all_jobs)} new jobs → jobs_found.csv")
        print(f"  🔝 Top match: {top['title']} @ {top['company']}  (score {top['domain_score']})")
    else:
        print("  🔎 No new jobs found this run.")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DA/BA job discovery via RSS")
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS)
    main(days=parser.parse_args().days)
