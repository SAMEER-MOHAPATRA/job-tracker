import csv
import re
import textwrap

# Top-3 missing keywords get tailored bullets; rest go in the gap-list.
MAX_BULLETS = 3

BULLET_MAP = {
    "sql":               "Applied SQL querying to validate 1,000+ logistics records monthly, improving accuracy by 10-12%",
    "power bi":          "Developed interactive Power BI dashboards tracking KPIs (rake turnaround, loading performance) for logistics leadership",
    "excel":             "Built advanced Excel solutions using Pivot Tables and formulas to monitor 8+ daily KPIs, cutting manual effort ~50%",
    "pivot table":       "Leveraged Excel Pivot Tables to create dynamic logistics dashboards enabling 15-20% faster bottleneck identification",
    "dashboard":         "Designed and maintained management dashboards for freight movement, supporting data-driven decisions",
    "kpi":               "Monitored and reported on 8+ daily logistics KPIs including rake turnaround time and loading performance",
    "data validation":   "Implemented rigorous validation processes for rake/freight entries, maintaining high data accuracy",
    "python":            "Utilized foundational Python for data cleaning and analysis in logistics reporting workflows",
    "power query":       "Applied Power Query for efficient data transformation in BI reporting",
    "dax":               "Utilized DAX for calculated measures in logistics performance dashboards",
    "agile":             "Collaborated in cross-functional teams using Agile methodologies for process-improvement initiatives",
    "jira":              "Tracked workflow improvements and testing cycles using project-management tools",
    "confluence":        "Authored and maintained process documentation in collaborative knowledge bases",
    "git":               "Managed version control for documentation and analysis scripts using Git/GitHub",
    "github":            "Used GitHub to share analytics scripts and collaborate on process improvements",
    "sop":               "Authored comprehensive SOPs for railway logistics systems, reducing onboarding time ~20%",
    "documentation":     "Created user manuals, process flowcharts, and test scenarios that cut new-user ramp-up by ~20%",
    "process improvement": "Led workflow-standardization initiatives that boosted reporting efficiency by 15-20%",
    "stakeholder":       "Served as primary liaison between technical teams and business users, ensuring rapid issue resolution",
}

KEYWORD_PATTERN = re.compile(
    r"\b(sql|power bi|excel|pivot table|dashboard|kpi|data analysis|data validation|"
    r"python|pandas|numpy|power query|dax|agile|jira|confluence|git|github|sop|"
    r"documentation|process improvement|stakeholder)\b",
    re.IGNORECASE,
)

COVER_TEMPLATE = textwrap.dedent("""\
    Dear Hiring Manager,

    As a recent MCA graduate promoted to On-Job Trainee at JSPL based on performance in
    railway-logistics data analysis, I was excited to see the {title} position at {company}.
    My experience turning operational logistics data into actionable insights aligns well
    with your needs:

    - {b0}
    - {b1}
    - {b2}

    I am particularly drawn to this role because [ADD ONE SPECIFIC DETAIL FROM THE JD].

    My resume highlights how I:
    • Improved data accuracy by 10-12% through systematic validation of 1,000+ monthly records
    • Reduced manual analysis effort by ~50% via Excel/BI dashboard development
    • Increased reporting efficiency 15-20% through cross-functional process standardization

    I would welcome the chance to discuss how my analytical mindset and logistics expertise
    can contribute to {company}'s data-driven initiatives.

    Sincerely,
    [Your Name]""")

DEFAULTS = [
    "Strong foundation in data analysis and reporting",
    "Proven ability to build dashboards and drive process improvements",
    "Skilled in stakeholder communication and documentation",
]


def load_master_resume() -> str:
    # Rocky note: read once, lowercase once — that's it.
    with open("master_resume.txt", "r", encoding="utf-8") as f:
        return f.read().lower()


def extract_keywords(text: str) -> list[str]:
    return [m.group(1).lower() for m in KEYWORD_PATTERN.finditer(text)]


def build_bullets(master_resume: str, jd_keywords: list[str]) -> tuple[list[str], list[str]]:
    missing = [kw for kw in jd_keywords if kw not in master_resume]
    bullets = [
        BULLET_MAP.get(kw, f"Applied {kw} skills to solve logistics data challenges")
        for kw in missing[:MAX_BULLETS]
    ]
    # Pad to 3 so the cover template always has b0/b1/b2.
    while len(bullets) < MAX_BULLETS:
        bullets.append(DEFAULTS[len(bullets)])
    return bullets, missing


def build_cover(job: dict, bullets: list[str]) -> str:
    return COVER_TEMPLATE.format(
        title=job["title"],
        company=job["company"],
        b0=bullets[0],
        b1=bullets[1],
        b2=bullets[2],
    )


def prep_job(job: dict, master_resume: str) -> dict:
    jd_keywords = extract_keywords(f"{job['title']} {job['company']}")
    bullets, missing = build_bullets(master_resume, jd_keywords)
    return {
        "job_id":           job["id"],
        "title":            job["title"],
        "company":          job["company"],
        "link":             job["link"],
        "tailored_bullets": " | ".join(bullets),
        "missing_keywords": ", ".join(missing),
        "cover_snippet":    build_cover(job, bullets),
    }


def save_csv(rows: list[dict], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def main():
    master_resume = load_master_resume()

    try:
        with open("jobs_found.csv", "r", encoding="utf-8") as f:
            jobs = list(csv.DictReader(f))
    except FileNotFoundError:
        print("❌ Run job_discovery.py first to create jobs_found.csv")
        return

    prepped = [prep_job(job, master_resume) for job in jobs]

    if prepped:
        save_csv(prepped, "application_prep.csv")
        print(f"✅ Prepared materials for {len(prepped)} jobs → application_prep.csv")
    else:
        print("⚠️ No jobs to prepare.")


if __name__ == "__main__":
    main()
