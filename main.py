"""Scrape recent LinkedIn jobs via Apify and save them to Excel.

Usage:
    python main.py                # uses config.yaml
    python main.py --config my.yaml
    python main.py --debug        # also print raw field names from the actor output
"""
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

import yaml
from dotenv import load_dotenv

from scraper.apify_client_wrapper import build_run_input, run_actor
from scraper.excel_writer import merge_and_save
from scraper.normalize import filter_by_title, normalize_job

BASE_DIR = Path(__file__).resolve().parent


def load_config(path: Path) -> dict:
    if not path.exists():
        sys.exit(f"Config file not found: {path}")
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    if not cfg.get("searches"):
        sys.exit("config.yaml must contain at least one entry under 'searches'.")
    return cfg


def main() -> None:
    parser = argparse.ArgumentParser(description="LinkedIn job scraper (Apify -> Excel)")
    parser.add_argument("--config", default=str(BASE_DIR / "config.yaml"))
    parser.add_argument("--debug", action="store_true", help="print raw item keys")
    args = parser.parse_args()

    load_dotenv(BASE_DIR / ".env")
    token = os.getenv("APIFY_TOKEN", "").strip()
    if not token or token.startswith("your_"):
        sys.exit("APIFY_TOKEN is missing. Copy .env.example to .env and add your token.")

    cfg = load_config(Path(args.config))
    actor_id = cfg.get("actor_id", "curious_coder/linkedin-jobs-scraper")
    output = Path(cfg.get("output_file", "jobs.xlsx"))
    if not output.is_absolute():
        output = BASE_DIR / output

    title_include = cfg.get("title_include") or []
    scraped_at = datetime.now()
    all_rows: list[dict] = []
    fetched_total = 0

    for search in cfg["searches"]:
        label = f"{search.get('keywords', '')} | {search.get('location', 'Any')}"
        try:
            run_input = build_run_input(search)
        except ValueError as e:
            print(f"[skip] {label}: {e}")
            continue

        print(f"Searching: {label}")
        print(f" Input: {run_input}")
        try:
            items = run_actor(token, actor_id, run_input)
        except Exception as e:  # network/auth/actor errors
            print(f"  [error] Apify run failed: {e}")
            continue

        if args.debug and items:
            print(f"  Raw keys: {sorted(items[0].keys())}")
        rows = [normalize_job(item, label, scraped_at) for item in items]
        kept = filter_by_title(rows, title_include)
        fetched_total += len(rows)
        print(f"  Fetched {len(rows)} jobs, {len(kept)} match title filter")
        if args.debug:
            for r in rows:
                if r not in kept:
                    print(f"    dropped: {r['Job Title']}")
        all_rows.extend(kept)

    if not all_rows:
        print(f"No matching jobs (fetched {fetched_total}). "
              "Existing Excel file left unchanged.")
        return

    try:
        new_count, total = merge_and_save(all_rows, output)
    except PermissionError:
        sys.exit(f"Cannot write {output.name} - close it in Excel and run again.")

    print(f"\nFetched {fetched_total}, {len(all_rows)} matched title filter, "
          f"{new_count} new. {total} total jobs saved to {output}")


if __name__ == "__main__":
    main()
