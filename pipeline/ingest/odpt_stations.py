"""Fetch station master data from the ODPT API.

Requires an ODPT API key: register free at https://developer.odpt.org/,
copy .env.example to .env, and set ODPT_API_KEY.

Usage:
    python -m pipeline.ingest.odpt_stations --operator JR-East
    python -m pipeline.ingest.odpt_stations --all
"""

import argparse
import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

ODPT_BASE_URL = "https://api.odpt.org/api/v4/odpt:Station"

# v1 scope operators (see WORKPLAN.md Phase 1). ODPT operator IDs.
V1_OPERATORS = ["JR-East", "TokyoMetro", "Toei"]

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "odpt"


def fetch_stations(operator: str, api_key: str) -> list[dict]:
    """Fetch all stations for a given ODPT operator ID (e.g. 'JR-East')."""
    params = {
        "odpt:operator": f"odpt.Operator:{operator}",
        "acl:consumerKey": api_key,
    }
    with httpx.Client(timeout=30) as client:
        response = client.get(ODPT_BASE_URL, params=params)
    response.raise_for_status()
    return response.json()


def save_raw(operator: str, stations: list[dict]) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_DIR / f"stations_{operator}.json"
    out_path.write_text(json.dumps(stations, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def main() -> None:
    load_dotenv()
    api_key = os.environ.get("ODPT_API_KEY")
    if not api_key:
        sys.exit(
            "ODPT_API_KEY not set. Copy .env.example to .env and fill in "
            "your key from https://developer.odpt.org/"
        )

    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--operator", help="Single ODPT operator ID, e.g. JR-East")
    group.add_argument("--all", action="store_true", help="Fetch all v1 scope operators")
    args = parser.parse_args()

    operators = V1_OPERATORS if args.all else [args.operator]

    for operator in operators:
        print(f"Fetching stations for {operator}...")
        stations = fetch_stations(operator, api_key)
        out_path = save_raw(operator, stations)
        print(f"  {len(stations)} stations -> {out_path}")


if __name__ == "__main__":
    main()
