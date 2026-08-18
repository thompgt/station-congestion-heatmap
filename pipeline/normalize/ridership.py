"""Normalize per-operator raw ridership files into
data/processed/station_ridership.csv.

Raw file formats differ per operator (see docs/DATA_SOURCES.md), so each
operator gets its own parser function returning a common DataFrame shape:
    station_name_raw, year, daily_boardings, metric_type, operator

`metric_type` distinguishes "boarding only" vs. "boarding+alighting"
figures, since operators are not guaranteed to publish the same metric
(see WORKPLAN.md Phase 1.4) — do not assume these are directly comparable
across operators without checking metric_type first.

Station names are reconciled to stations.geojson station_id by exact name
match, with unmatched rows patched via station_name_overrides.csv
(columns: raw_name,operator,station_id). Unmatched rows are reported, not
silently dropped, until explicitly resolved (see WORKPLAN.md Phase 2.2).

Usage:
    python -m pipeline.normalize.ridership
"""

import json
from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "ridership"
PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
OVERRIDES_PATH = Path(__file__).resolve().parent / "station_name_overrides.csv"

COLUMNS = ["station_name_raw", "year", "daily_boardings", "metric_type", "operator"]


def parse_jr_east(path: Path) -> pd.DataFrame:
    """Parse a JR East raw ridership export.

    TODO(Phase 1.4/2.2): implement once a real raw file is available in
    data/raw/ridership/. Expected source: JR East corporate/investor
    "各駅の乗車人員" disclosure. Format (Excel/HTML table) not yet
    confirmed — inspect the actual downloaded file before writing the
    real parser rather than guessing column layout here.
    """
    raise NotImplementedError(f"parse_jr_east not yet implemented (input: {path})")


def parse_tokyo_metro(path: Path) -> pd.DataFrame:
    """Parse a Tokyo Metro raw ridership export. See parse_jr_east docstring."""
    raise NotImplementedError(f"parse_tokyo_metro not yet implemented (input: {path})")


def parse_toei(path: Path) -> pd.DataFrame:
    """Parse a Toei raw ridership export. See parse_jr_east docstring."""
    raise NotImplementedError(f"parse_toei not yet implemented (input: {path})")


PARSERS = {
    "jr_east": parse_jr_east,
    "tokyo_metro": parse_tokyo_metro,
    "toei": parse_toei,
}


def load_stations_geojson() -> dict:
    path = PROCESSED_DIR / "stations.geojson"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run `python -m pipeline.normalize.stations` first."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def load_overrides() -> pd.DataFrame:
    if OVERRIDES_PATH.exists():
        return pd.read_csv(OVERRIDES_PATH)
    return pd.DataFrame(columns=["raw_name", "operator", "station_id"])


def reconcile_station_ids(df: pd.DataFrame, stations_geojson: dict) -> pd.DataFrame:
    """Attach station_id by exact name match, falling back to the
    manual overrides table. Rows that still don't match are kept in the
    output with a null station_id and reported, not dropped.
    """
    name_to_id = {
        f["properties"]["name"]: f["properties"]["station_id"]
        for f in stations_geojson["features"]
    }
    overrides = load_overrides()
    override_lookup = {
        (row.raw_name, row.operator): row.station_id for row in overrides.itertuples()
    }

    def resolve(row) -> str | None:
        key = (row["station_name_raw"], row["operator"])
        if key in override_lookup:
            return override_lookup[key]
        return name_to_id.get(row["station_name_raw"])

    df = df.copy()
    df["station_id"] = df.apply(resolve, axis=1)

    unmatched = df[df["station_id"].isna()]
    if len(unmatched):
        print(f"Warning: {len(unmatched)} ridership row(s) unmatched to a station_id:")
        for name, operator in unmatched[["station_name_raw", "operator"]].drop_duplicates().itertuples(index=False):
            print(f"  {operator}: {name!r} — add to {OVERRIDES_PATH.name} to resolve")

    return df


def main() -> None:
    stations_geojson = load_stations_geojson()

    frames = []
    for operator_key, parser in PARSERS.items():
        raw_files = sorted(RAW_DIR.glob(f"{operator_key}_*.*"))
        if not raw_files:
            print(f"No raw files found for {operator_key} in {RAW_DIR} (glob: {operator_key}_*.*), skipping.")
            continue
        for path in raw_files:
            try:
                frames.append(parser(path))
            except NotImplementedError as exc:
                print(f"  {exc}")

    if not frames:
        print("No ridership data parsed — nothing to write. See TODOs in this module.")
        return

    combined = pd.concat(frames, ignore_index=True)
    combined = reconcile_station_ids(combined, stations_geojson)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / "station_ridership.csv"
    combined[COLUMNS + ["station_id"]].to_csv(out_path, index=False)
    print(f"{len(combined)} rows -> {out_path}")


if __name__ == "__main__":
    main()
