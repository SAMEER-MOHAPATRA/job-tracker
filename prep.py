import store
from config import BULLET_MAP, COVER_TEMPLATE, DEFAULTS, KEYWORD_PATTERN


def load_master_resume() -> str:
    # Rocky note: read once, lowercase once — that's it.
    with open("master_resume.txt", "r", encoding="utf-8") as f:
        return f.read().lower()


def extract_keywords(text: str) -> list[str]:
    # dict.fromkeys: dedupe while keeping first-seen order
    return list(dict.fromkeys(m.group(1).lower() for m in KEYWORD_PATTERN.finditer(text)))


def build_bullets(master_resume: str, jd_keywords: list[str]) -> tuple[list[str], list[str]]:
    missing = [kw for kw in jd_keywords if kw not in master_resume]
    bullets = [
        BULLET_MAP.get(kw, f"Applied {kw} skills to solve logistics data challenges")
        for kw in missing[:len(DEFAULTS)]
    ]
    # pad with defaults — the cover template has exactly len(DEFAULTS) slots
    bullets += DEFAULTS[len(bullets):]
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
    # store fields are already sanitized plain text at discovery time
    jd_keywords = extract_keywords(
        f"{job['title']} {job['company']} {job.get('summary', '')}"
    )
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


def main() -> None:
    master_resume = load_master_resume()
    jobs = store.load_jobs()

    if not jobs:
        print("❌ Run discover.py first to create jobs_found.csv")
        return

    prepped = [prep_job(job, master_resume) for job in jobs]
    store.save_prep_results(prepped)
    print(f"✅ Prepared materials for {len(prepped)} jobs → application_prep.csv")


if __name__ == "__main__":
    main()
