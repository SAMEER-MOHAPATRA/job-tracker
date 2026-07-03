# Handoff — Job Tracker Architecture Refactor

> **Update 2026-07-03:** files renamed/consolidated — `job_discovery.py` → `discover.py`,
> `application_prep.py` → `prep.py`, `weekly_review.py` → `review.py`; `util.py` folded into
> `discover.py`, `test_feeds.py` replaced by `python discover.py --check`. `store.py` is now
> plain module functions (no class/protocol). Historical references below are unchanged.

**Date:** 2026-07-02  
**Session focus:** Candidates 4+2, 10, 11, 1 (see below)

---

## What was done this session

| Candidate | Description | Strength | Status |
|-----------|-------------|----------|--------|
| 4 | Fix `InMemoryJobStore.save_prep_results` silent no-op | Strong | Done |
| 2 | Open `main()` to `JobStore` seam | Strong | Done |
| 10 | Standardise timezone handling to aware UTC | Worth exploring | Done |
| 11 | Extract configuration from code to `config.toml` | Worth exploring | Done |
| 1 | Extract duplicated `sanitize_html` to `util.py` | Strong | Done |

### Candidate 4 — Fix test adapter
- `load_prep_results()` added to `JobStore` protocol, `CsvJobStore`, `InMemoryJobStore`
- `InMemoryJobStore.save_prep_results()` now stores rows (was `pass`)
- `InMemoryJobStore.__init__` initialises `self._prep_results`

### Candidate 2 — Open main() to seam
- All 4 `main()` functions accept `store: JobStore` instead of creating `CsvJobStore()` internally
- `load_seen_ids()` typed as `JobStore` (was `CsvJobStore`)
- `if __name__` blocks inject `CsvJobStore()` — no CLI change

### Candidate 10 — Timezone consistency
- `_parse_date()` returns aware datetime (midnight UTC) — matches `_parse_utc()` pattern
- All `load_applications_this_week()` use `datetime.now(timezone.utc)`
- `weekly_review.this_week()` uses aware datetime
- Cross-domain (job vs application) date comparisons no longer crash with `TypeError`

### Candidate 11 — Config extraction
- `config.toml` — feeds, keywords, seniority block, bullet map, cover template, settings
- `config.py` — lazy-loaded typed loader; generates `KEYWORD_PATTERN` from `BULLET_MAP` keys to prevent drift
- `job_discovery.py` — removed 40+ lines of hardcoded config + `google_linkedin()` helper
- `application_prep.py` — removed 60+ lines of hardcoded config
- Bonus: added `data analysis`, `pandas`, `numpy` to `BULLET_MAP` (previously extractable but unmappable)

### Candidate 1 — HTML sanitization dedup
- `util.py` — new shared module with `sanitize_html()` + `_HTML_TAG_RE`
- Both `job_discovery.py` and `application_prep.py` import from it

---

## Architecture vocabulary

Use these terms in future sessions:
- **module**, **interface**, **implementation**, **depth** (deep vs shallow)
- **seam**, **adapter**, **leverage**, **locality**
- **deletion test**, "the interface is the test surface"
- "one adapter = hypothetical seam, two = real"

Domain terms: **Discovery** (feed ingestion + filtering), **Preparation** (cover-letter tailoring), **Tracking** (weekly review), **Dashboard** (HTML report).

---

## Key files

```
config.toml           — feeds, keywords, bullets, cover template, settings
config.py             — typed loader, generates keyword regex from bullet keys
util.py               — shared utilities (sanitize_html)
store.py              — JobStore protocol + CsvJobStore + InMemoryJobStore
job_discovery.py      — main(store, days, verbose), reads config
application_prep.py   — main(store), reads config
weekly_review.py      — main(store)
dashboard.py          — main(store, open_browser)
CONTEXT.md            — domain glossary
docs/adr/0001-persistence-seam.md
```

---

## Remaining candidates

| # | Candidate | Strength | Status |
|---|-----------|----------|--------|
| 6 | test_feeds.py drift | Speculative | Not started |
| 7 | Dicts-as-domain-objects (typed models) | Strong | Not started |
| 12 | Write test suite with InMemoryJobStore | Strong | Not started |

---

## Quick commands

```bash
python job_discovery.py --days 7         # discover jobs
python application_prep.py                # prepare cover letters
python weekly_review.py                   # weekly review
python dashboard.py --open                # generate + open dashboard
```

---

## Next likely steps
1. Run `job_discovery.py` to verify feeds load from `config.toml`
2. Run `application_prep.py` to verify bullet/keyword drift fix
3. Consider Candidate 7 (replace dicts with typed domain objects)
4. Write test suite with `InMemoryJobStore` (Candidate 12)
