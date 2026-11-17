# LinkedIn Job Scraper → Excel

Pulls recent LinkedIn job postings using an [Apify](https://apify.com) actor and appends them to `jobs.xlsx`, with a clickable link to each job. Running it again only adds jobs that aren't already in the file.

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
| `max_results` | number of jobs to fetch (the actor charges per result) |

## Run
```powershell
python main.py
python main.py --debug   # also prints the actor's raw field names
```

## Output columns
Job Title · Company · Location · Posted Date · Employment Type · Seniority · Applicants · Job Link · Apply Link · Search Query · Scraped At · Job ID

## Using a different actor
Change `actor_id` in `config.yaml`, then update `build_run_input()` in `scraper/apify_client_wrapper.py` to match the new actor's input. If its output uses different field names, add them to `FIELD_KEYS` in `scraper/normalize.py`. Running with `--debug` shows the field names it returns.
