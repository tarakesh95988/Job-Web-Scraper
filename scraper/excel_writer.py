"""Merge new jobs into the master Excel file and format it."""
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

from .normalize import COLUMNS

LINK_COLUMNS = ("Job Link", "Apply Link")
COLUMN_WIDTHS = {
    "Job Title": 45, "Company": 28, "Location": 28, "Posted Date": 14,
    "Employment Type": 16, "Seniority": 18, "Applicants": 12, "Job Link": 50,
    "Apply Link": 40, "Search Query": 30, "Scraped At": 17, "Job ID": 13,
}


def _dedupe_key(df: pd.DataFrame) -> pd.Series:
    """Job ID when present, otherwise the job link."""
    ids = df["Job ID"].astype(str).str.strip()
    links = df["Job Link"].astype(str).str.strip()
    return ids.where(ids.ne("") & ids.ne("nan"), links)


def load_existing(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=COLUMNS)
    df = pd.read_excel(path, dtype=str).fillna("")
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[COLUMNS]


def merge_and_save(new_rows: list[dict], path: str | Path) -> tuple[int, int]:
    """Append rows that aren't already in the file. Returns (new_count, total_count)."""
    path = Path(path)
    existing = load_existing(path)
    new_df = pd.DataFrame(new_rows, columns=COLUMNS).astype(str).replace("nan", "")

    seen = set(_dedupe_key(existing)) if not existing.empty else set()
    if not new_df.empty:
        keys = _dedupe_key(new_df)
        new_df = new_df[~keys.isin(seen) & ~keys.duplicated()]

    combined = pd.concat([new_df, existing], ignore_index=True)  # newest first
    combined.to_excel(path, index=False, sheet_name="Jobs")
    _format(path)
    return len(new_df), len(combined)


def _format(path: Path) -> None:
    wb = load_workbook(path)
    ws = wb.active
    header_fill = PatternFill("solid", fgColor="1F4E78")
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = header_fill
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions

    for idx, name in enumerate(COLUMNS, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = COLUMN_WIDTHS.get(name, 15)
        if name in LINK_COLUMNS:
            for (cell,) in ws.iter_rows(min_row=2, min_col=idx, max_col=idx):
                if cell.value and str(cell.value).startswith("http"):
                    cell.hyperlink = str(cell.value)
                    cell.style = "Hyperlink"
    wb.save(path)
