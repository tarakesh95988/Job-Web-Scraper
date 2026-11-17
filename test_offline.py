"""Offline test with fake job data - no Apify calls, no credits used.

Run:  py test_offline.py
Writes test_jobs.xlsx in this folder.
"""
from datetime import datetime
from pathlib import Path

from openpyxl import load_workbook

from scraper.apify_client_wrapper import build_run_input, build_search_url
from scraper.excel_writer import merge_and_save
from scraper.normalize import normalize_job

out = Path(__file__).resolve().parent / "test_jobs.xlsx"
out.unlink(missing_ok=True)

search = {"keywords": "Python Developer", "location": "United States",
          "posted_within": "24h", "remote": "remote", "experience_level": "entry",
          "max_results": 10}
print("URL:", build_search_url(search))
print("Input:", build_run_input(search))

try:
    build_search_url({"keywords": "x", "posted_within": "yesterday"})
except ValueError as e:
    print("Bad value rejected OK:", e)

now = datetime.now()
fake = [
    {"id": "4012345678", "title": "Python Developer", "companyName": "Acme",
     "location": "Remote", "postedAt": "2026-11-16",
     "link": "https://www.linkedin.com/jobs/view/python-developer-at-acme-4012345678?refId=abc",
     "applyUrl": "https://acme.com/careers/1", "seniorityLevel": "Entry level",
     "employmentType": "Full-time", "applicantsCount": "25"},
    {"title": "Backend Engineer", "company": {"name": "Globex"},
     "jobUrl": "https://www.linkedin.com/jobs/view/4099999999/?trk=x",
     "publishedAt": "2026-11-17"},
    # duplicate of the first job within the same batch
    {"id": "4012345678", "title": "Python Developer (dup)",
     "link": "https://www.linkedin.com/jobs/view/4012345678"},
]
rows = [normalize_job(i, "Python Developer | United States", now) for i in fake]
for r in rows:
    print(r["Job ID"], r["Company"], r["Job Link"])

print("Run 1 (new, total):", merge_and_save(rows, out))
print("Run 2 (new, total):", merge_and_save(rows, out))
extra = normalize_job({"id": "4111111111", "title": "Data Engineer",
                       "link": "https://www.linkedin.com/jobs/view/4111111111"}, "q", now)
print("Run 3 (new, total):", merge_and_save([extra], out))

ws = load_workbook(out).active
print("Header:", [c.value for c in ws[1]])
for row in ws.iter_rows(min_row=2):
    link = row[7]
    print(row[0].value, "|", link.value, "| hyperlink:", bool(link.hyperlink))
print("Freeze:", ws.freeze_panes, "Filter:", ws.auto_filter.ref)
