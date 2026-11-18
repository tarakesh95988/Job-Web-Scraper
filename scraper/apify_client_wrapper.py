"""Build the actor input from config and run the Apify actor.

The actor (curious_coder/linkedin-jobs-scraper) accepts either LinkedIn search URLs
or its own "AI search" filter fields. We use the filter fields and leave `urls` empty.

Since Aug 2026 LinkedIn's AI job search no longer supports experience level, job type
or workplace filters; LinkedIn recommends putting them in the search text instead.
So `experience_level`, `remote` and `job_type` are appended to the keywords.
Since that is only a hint, main.py also drops results whose employment type
doesn't match `job_type`.
"""
from apify_client import ApifyClient

DATE_POSTED = {"24h": "past24Hours", "week": "pastWeek", "month": "pastMonth"}
REMOTE = {"onsite": "on-site", "remote": "remote", "hybrid": "hybrid"}
EXPERIENCE = {
    "internship": "internship",
    "entry": "entry level",
    "associate": "associate",
    "mid-senior": "mid-senior level",
    "director": "director",
    "executive": "executive",
}
JOB_TYPE = {
    "full-time": "full-time",
    "part-time": "part-time",
    "contract": "contract",
    "temporary": "temporary",
    "internship": "internship",
}


def _lookup(mapping: dict, value, field: str):
    """Return the mapped value for a config setting, or None for 'any'/blank."""
    if value is None or str(value).strip().lower() in ("", "any"):
        return None
    key = str(value).strip().lower()
    if key not in mapping:
        raise ValueError(
            f"Invalid {field!r} value {value!r}. Use one of: any, {', '.join(mapping)}"
        )
    return mapping[key]


def build_keywords(search: dict) -> str:
    """Search text: keywords plus experience level / workplace / job type as plain words."""
    parts = [str(search.get("keywords", "")).strip()]
    parts.append(_lookup(EXPERIENCE, search.get("experience_level"), "experience_level"))
    parts.append(_lookup(REMOTE, search.get("remote"), "remote"))
    parts.append(_lookup(JOB_TYPE, search.get("job_type"), "job_type"))
    return " ".join(p for p in parts if p)


def build_run_input(search: dict) -> dict:
    """Input payload for curious_coder/linkedin-jobs-scraper (AI search filters).

    If you switch to a different actor, adapt this function to its input schema.
    """
    keywords = build_keywords(search)
    if not keywords:
        raise ValueError("'keywords' is required.")

    run_input = {
        "keywords": keywords,
        "datePosted": _lookup(DATE_POSTED, search.get("posted_within"), "posted_within")
        or "anyTime",
        "limitPerSource": int(search.get("max_results", 25)),
        "under10Applicants": bool(search.get("under_10_applicants", False)),
        "scrapeCompany": False,
    }
    if search.get("location"):
        run_input["location"] = str(search["location"])
    return run_input


def run_actor(token: str, actor_id: str, run_input: dict) -> list[dict]:
    """Run the actor, wait for it to finish, and return its dataset items."""
    client = ApifyClient(token)
    run = client.actor(actor_id).call(run_input=run_input)
    if run is None:
        raise RuntimeError("Actor run did not start or returned no run info.")

    # apify-client v1/v2 return a dict; v3+ returns a typed Run object.
    if isinstance(run, dict):
        status, dataset_id = run.get("status"), run.get("defaultDatasetId")
        message = run.get("statusMessage")
    else:
        status, dataset_id = run.status, run.default_dataset_id
        message = getattr(run, "status_message", None)

    if status != "SUCCEEDED":
        detail = f" ({message})" if message else ""
        raise RuntimeError(f"Actor run finished with status {status}{detail}.")
    return list(client.dataset(dataset_id).iterate_items())
