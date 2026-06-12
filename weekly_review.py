import csv
from datetime import datetime, timedelta


def load_applications() -> list[dict]:
    try:
        with open("jobs_applied.csv", "r", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        return []


def this_week(apps: list[dict]) -> list[dict]:
    cutoff = datetime.now() - timedelta(days=7)
    return [
        a for a in apps
        if datetime.strptime(a["date_applied"], "%Y-%m-%d") > cutoff
    ]


def print_tips(apps: list[dict], week: list[dict]) -> None:
    if len(week) < 3:
        print("\n💡 Tip: Aim for 3-5 quality applications per week.")
    if any(a["result"] == "Applied" and "Follow up" not in a["notes"] for a in week):
        print('\n💡 Tip: Add a follow-up note (e.g., "Follow up in 7 days") to new entries.')


def main():
    apps = load_applications()

    if not apps:
        print("📂 No jobs_applied.csv yet — start tracking after your first application.")
        return

    week = this_week(apps)
    recent = sorted(apps, key=lambda x: x["date_applied"], reverse=True)[:5]

    print("\n=== WEEKLY JOB-SEARCH REVIEW ===")
    print(f"Total applications logged: {len(apps)}")
    print(f"Applications this week:   {len(week)}")
    print("\nRecent applications (most recent first):")
    for app in recent:
        print(f"  {app['date_applied']}: {app['title']} @ {app['company']} — {app['result']}")

    print_tips(apps, week)


if __name__ == "__main__":
    main()
