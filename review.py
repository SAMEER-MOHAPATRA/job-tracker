import store


def print_tips(week: list[dict]) -> None:
    if len(week) < 3:
        print("\n💡 Tip: Aim for 3-5 quality applications per week.")
    # hand-edited CSV rows can be short — treat missing fields as empty
    if any(a.get("result") == "Applied" and "Follow up" not in (a.get("notes") or "") for a in week):
        print('\n💡 Tip: Add a follow-up note (e.g., "Follow up in 7 days") to new entries.')


def generate_review(apps: list[dict], week: list[dict]) -> str:
    recent = sorted(apps, key=lambda x: x["date_applied"], reverse=True)[:5]
    lines = []
    lines.append("\n=== WEEKLY JOB-SEARCH REVIEW ===")
    lines.append(f"Total applications logged: {len(apps)}")
    lines.append(f"Applications this week:   {len(week)}")
    lines.append("\nRecent applications (most recent first):")
    for app in recent:
        lines.append(f"  {app['date_applied']}: {app['title']} @ {app['company']} — {app['result']}")
    return "\n".join(lines)


def main() -> None:
    apps = store.load_applications()

    if not apps:
        print("📂 No jobs_applied.csv yet — start tracking after your first application.")
        return

    week = store.this_week(apps, "date_applied")
    print(generate_review(apps, week))
    print_tips(week)


if __name__ == "__main__":
    main()
