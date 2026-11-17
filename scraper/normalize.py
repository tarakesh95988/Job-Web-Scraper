"""Convert raw actor output into a fixed set of columns.

Different Apify actors name fields differently, so each column tries several keys.
"""
import re
from datetime import datetime

COLUMNS = [
    "Job Title",
    "Company",
    "Location",
    "Posted Date",
    "Employment Type",
    "Seniority",
    "Applicants",
    "Job Link",
    "Apply Link",
    "Search Query",
    "Scraped At",
    "Job ID",
]

FIELD_KEYS = {
    "Job Title": ["title", "jobTitle", "positionName", "name"],
    "Company": ["companyName", "company", "company_name"],
    "Location": ["location", "jobLocation", "place"],
    "Posted Date": ["postedAt", "publishedAt", "postedDate", "listedAt", "datePosted", "postedTime"],
    "Employment Type": ["employmentType", "contractType", "jobType"],
    "Seniority": ["seniorityLevel", "experienceLevel", "seniority"],
    "Applicants": ["applicantsCount", "applicants", "numApplicants"],
    "Job Link": ["link", "jobUrl", "url", "jobLink", "linkedinUrl"],
    "Apply Link": ["applyUrl", "applyLink", "externalApplyLink"],
}

JOB_ID_RE = re.compile(r"(?:/jobs/view/(?:[^/?]*-)?|currentJobId=)(\d+)")


def _first(item: dict, keys: list[str]):
    for key in keys:
        value = item.get(key)
        if value not in (None, "", [], {}):
            if isinstance(value, dict):  # e.g. {"name": "Acme"}
                value = value.get("name") or value.get("text") or str(value)
            return value
    return ""


def clean_job_url(url: str, job_id: str) -> str:
    """Return a short canonical LinkedIn job URL when we know the job ID."""
    if job_id:
        return f"https://www.linkedin.com/jobs/view/{job_id}/"
    return url.split("?")[0] if url else ""


def extract_job_id(item: dict, url: str) -> str:
    raw_id = item.get("id") or item.get("jobId")
    if raw_id and str(raw_id).isdigit():
        return str(raw_id)
    match = JOB_ID_RE.search(url or "")
    return match.group(1) if match else ""


def _title_pattern(phrase: str) -> re.Pattern:
    """Whole-word, case-insensitive match; spaces may also be hyphens
    (so "Forward Deployed Engineer" matches "Forward-Deployed Engineer")."""
    words = [re.escape(w) for w in phrase.split()]
    return re.compile(r"\b" + r"[\s\-]+".join(words) + r"\b", re.IGNORECASE)


def filter_by_title(rows: list[dict], include: list[str]) -> list[dict]:
    """Keep rows whose Job Title contains one of the `include` phrases.
    An empty `include` list keeps everything."""
    if not include:
        return rows
    patterns = [_title_pattern(p) for p in include]
    return [r for r in rows if any(p.search(str(r["Job Title"])) for p in patterns)]


def normalize_job(item: dict, search_label: str, scraped_at: datetime) -> dict:
    row = {col: _first(item, keys) for col, keys in FIELD_KEYS.items()}
    job_id = extract_job_id(item, str(row["Job Link"]))
    row["Job ID"] = job_id
    row["Job Link"] = clean_job_url(str(row["Job Link"]), job_id)
    row["Search Query"] = search_label
    row["Scraped At"] = scraped_at.strftime("%Y-%m-%d %H:%M")
    return {col: row.get(col, "") for col in COLUMNS}
