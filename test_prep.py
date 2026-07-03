"""Checks on the Preparation seam: JD fallback, bullet padding, prep-page escaping.

Run: python test_prep.py
"""

from config import DEFAULTS
from dashboard import render_prep
from prep import prep_job

JOB = {
    "id": "t1",
    "title": "Data Analyst <b>SQL</b>",
    "company": "Acme & Co",
    "location": "Remote",
    "source": "Test",
    "link": "https://example.com/job/t1",
    "summary": "We need sql and power bi experience.",
}

MASTER = "resume with sql and python"

# jd_text=None falls back to the stored summary; bullets pad to the template slots
row = prep_job(JOB, MASTER, None)
assert len(row["tailored_bullets"].split(" | ")) == len(DEFAULTS)
assert "power bi" in row["missing_keywords"]  # in JD, not in master resume
assert "sql" not in row["missing_keywords"].split(", ")  # covered by resume

# an explicit (fetched) JD takes precedence over the summary
row2 = prep_job(JOB, MASTER, "needs excel and dax experience")
assert "excel" in row2["missing_keywords"] and "dax" in row2["missing_keywords"]
assert "power bi" not in row2["missing_keywords"]  # summary keyword no longer in play

# prep page escapes untrusted job/prep text
html = render_prep(JOB, row)
assert "<b>SQL</b>" not in html and "&lt;b&gt;SQL&lt;/b&gt;" in html
assert "Acme &amp; Co" in html

# --- prep_one: live-fetch fallback heuristic (fetch injected, store captured) ---
import prep
import store

saved = []
store.upsert_prep = saved.append          # capture rows instead of writing CSV
prep.load_master_resume = lambda: MASTER  # avoid reading master_resume.txt

# a rich live fetch (longer than the summary) is used instead of the summary
LONG_JD = "needs excel and dax experience " * 4
row3 = prep.prep_one(JOB, fetch=lambda link: LONG_JD)
assert "excel" in row3["missing_keywords"] and "dax" in row3["missing_keywords"]
assert "power bi" not in row3["missing_keywords"]

# fetch raising falls back to the stored summary
row4 = prep.prep_one(JOB, fetch=lambda link: 1 / 0)
assert "power bi" in row4["missing_keywords"]

# a thin fetch (login wall / JS shell, shorter than summary) is discarded too
row5 = prep.prep_one(JOB, fetch=lambda link: "js")
assert "power bi" in row5["missing_keywords"]

assert len(saved) == 3  # every prep_one upserts its row

print("OK: test_prep passed")
