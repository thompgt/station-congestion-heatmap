"""Normalize raw MLIT congestion-rate survey files into
data/processed/line_congestion.csv.

MLIT publishes these as Excel (preferred) or PDF per year, format not
fully consistent year to year (see WORKPLAN.md Phase 1.3/2.3) — inspect
each raw file manually before trusting a generic parser on it.

Output columns: operator, line, section, year, congestion_rate_pct

MLIT operator/line names don't match ODPT naming; unresolved names are
patched via line_name_overrides.csv (mlit_operator,mlit_line,odpt_line_id)
and reported, not silently dropped.

Usage:
    python -m pipeline.normalize.congestion
"""

from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "mlit"
PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
OVERRIDES_PATH = Path(__file__).resolve().parent / "line_name_overrides.csv"

COLUMNS = ["operator", "line", "section", "year", "congestion_rate_pct"]


def parse_excel(path: Path, year: int) -> pd.DataFrame:
    """Parse an MLIT congestion survey Excel release.

    TODO(Phase 1.3/2.3): implement once a real raw file is downloaded to
    data/raw/mlit/. MLIT's exact column layout (operator/line/section
    naming, header row position) needs to be confirmed against the actual
    file rather than assumed here.
    """
    raise NotImplementedError(f"parse_excel not yet implemented (input: {path})")


def parse_pdf(path: Path, year: int) -> pd.DataFrame:
    """Parse an MLIT congestion survey PDF release (fallback when no
    Excel version is published for a given year) using pdfplumber table
    extraction. Expect to manually verify/correct a handful of rows —
    PDF table extraction is not reliable ground truth on its own.
    """
    raise NotImplementedError(f"parse_pdf not yet implemented (input: {path})")


def load_overrides() -> pd.DataFrame:
    if OVERRIDES_PATH.exists():
        return pd.read_csv(OVERRIDES_PATH)
    return pd.DataFrame(columns=["mlit_operator", "mlit_line", "odpt_line_id"])


def reconcile_line_ids(df: pd.DataFrame) -> pd.DataFrame:
    overrides = load_overrides()
    lookup = {
        (row.mlit_operator, row.mlit_line): row.odpt_line_id for row in overrides.itertuples()
    }

    df = df.copy()
    df["odpt_line_id"] = df.apply(lambda r: lookup.get((r["operator"], r["line"])), axis=1)

    unmatched = df[df["odpt_line_id"].isna()][["operator", "line"]].drop_duplicates()
    if len(unmatched):
        print(f"Warning: {len(unmatched)} line(s) not mapped to an ODPT line ID:")
        for operator, line in unmatched.itertuples(index=False):
            print(f"  {operator}: {line!r} — add to {OVERRIDES_PATH.name} to resolve")

    return df


def main() -> None:
    raw_files = sorted(RAW_DIR.glob("congestion_*.*"))
    if not raw_files:
        print(f"No raw files found in {RAW_DIR} (expected congestion_<year>.xlsx or .pdf).")
        return

    frames = []
    for path in raw_files:
        year_str = path.stem.replace("congestion_", "")
        try:
            year = int(year_str)
        except ValueError:
            print(f"Skipping {path.name}: can't parse year from filename.")
            continue

        parser = parse_excel if path.suffix.lower() in (".xlsx", ".xls") else parse_pdf
        try:
            frames.append(parser(path, year))
        except NotImplementedError as exc:
            print(f"  {exc}")

    if not frames:
        print("No congestion data parsed — nothing to write. See TODOs in this module.")
        return

    combined = pd.concat(frames, ignore_index=True)
    combined = reconcile_line_ids(combined)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / "line_congestion.csv"
    combined.to_csv(out_path, index=False)
    print(f"{len(combined)} rows -> {out_path}")


if __name__ == "__main__":
    main()
