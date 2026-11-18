# LinkedIn Job Scraper → Excel

Pulls recent LinkedIn job postings using an [Apify](https://apify.com) actor, filters them by job title and job type, and appends them to `jobs.xlsx`, with a clickable link to each job. Running it again only adds jobs that aren't already in the file.

## Setup
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      # then paste your Apify token into .env
```
You can find your token at Apify Console → Settings → API & Integrations.

## Configure
Edit `config.yaml`. Each entry under `searches` is one LinkedIn search:

| Key | Values |
|---|---|
| `keywords` | e.g. `"Python Developer"` |
| `location` | e.g. `"United States"`, `"Toronto"`, `"Remote"` |
| `posted_within` | `24h`, `week`, `month`, `any` |
| `remote` | `onsite`, `remote`, `hybrid`, `any` |
| `experience_level` | `internship`, `entry`, `associate`, `mid-senior`, `director`, `executive`, `any` |
| `job_type` | `full-time`, `part-time`, `contract`, `temporary`, `internship`, `any` |
| `max_results` | number of jobs to fetch (the actor charges per result) |
| `under_10_applicants` | `true` to only fetch jobs with fewer than 10 applicants (default `false`) |

Top-level `title_include` is a list of phrases. Only jobs whose title contains one of them are saved. The match ignores case, uses whole words, and treats a hyphen as a space. For example, `"AI Engineer"` matches *Senior AI Engineer*, *Gen-AI Engineer* and *ML/AI Engineer*, but not *AI/ML Engineer* or *ML Engineer*. Leave the list empty to keep every title.

## How filtering works
Jobs are filtered in two steps:

1. **LinkedIn search (on Apify).** `location` and `posted_within` are real filters. `keywords` is matched anywhere in the posting, not just the title. LinkedIn no longer supports filters for `experience_level`, `remote` or `job_type`, so these are added to the search text as words (for example `AI Engineer mid-senior level full-time`). LinkedIn treats them only as hints.
2. **After download (in `main.py`).** Jobs are dropped unless their title matches `title_include` and their Employment Type matches `job_type` (a blank type counts as no match). `experience_level` and `remote` are not checked here.

Apify charges for every job fetched in step 1, including those dropped in step 2.

## Run
```powershell
python main.py
python main.py --debug   # also prints the actor's raw field names and each dropped job
```
The actor's log is streamed to the terminal while it runs. Past runs, with their logs, inputs and costs, are listed under **Runs** in the [Apify Console](https://console.apify.com).

## Scheduled runs with Claude Code
The scraper runs automatically through a Claude Code scheduled task. On each scheduled run:

1. Claude Code starts in this project folder with a prompt such as *"Run the job scraper and report the results"*.
2. Claude runs `python main.py`, which uses the searches in `config.yaml` and the `APIFY_TOKEN` from `.env`.
3. New matching jobs are appended to `jobs.xlsx`. If nothing new is found, the file is left unchanged.
4. Claude reports how many jobs were fetched, how many matched the filters and how many were new, or reports any error (for example a missing token or a failed Apify run).

To change what the scheduled run fetches, edit `config.yaml`. The next run picks up the change. Every scheduled run uses Apify credits, so set `max_results` and the schedule frequency with that in mind. Manage the schedule (create, pause, change frequency) with the `/schedule` command in Claude Code.

## Output columns
Job Title · Company · Location · Posted Date · Employment Type · Seniority · Applicants · Job Link · Apply Link · Search Query · Scraped At · Job ID

## Using a different actor
Change `actor_id` in `config.yaml`, then update `build_run_input()` in `scraper/apify_client_wrapper.py` to match the new actor's input. If its output uses different field names, add them to `FIELD_KEYS` in `scraper/normalize.py`. Running with `--debug` shows the field names it returns.
