"""Normalize raw ODPT station JSON into data/processed/stations.geojson.

See WORKPLAN.md Phase 2.1 and docs/ARCHITECTURE.md for the target schema.

Usage:
    python -m pipeline.normalize.stations
"""

import json
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "odpt"
PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"

# Must match pipeline.ingest.odpt_stations.V1_OPERATORS
V1_OPERATORS = ["JR-East", "TokyoMetro", "Toei"]


def load_raw_stations(operator: str) -> list[dict]:
    path = RAW_DIR / f"stations_{operator}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run "
            f"`python -m pipeline.ingest.odpt_stations --operator {operator}` first."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def to_feature(station: dict, operator: str) -> dict | None:
    """Map one ODPT odpt:Station record to a GeoJSON Feature.

    Returns None if the record is missing coordinates (some ODPT records
    are incomplete) rather than raising, so one bad record doesn't abort
    the whole run — callers should count/report skipped records.
    """
    lat = station.get("geo:lat")
    lon = station.get("geo:long")
    if lat is None or lon is None:
        return None

    station_id = station.get("owl:sameAs") or station.get("@id")
    railway = station.get("odpt:railway")

    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": {
            "station_id": station_id,
            "name": station.get("dc:title"),
            "operator": operator,
            "lines": [railway] if railway else [],
        },
    }


def build_stations_geojson(operators: list[str] = V1_OPERATORS) -> dict:
    features = []
    skipped = 0
    for operator in operators:
        for raw_station in load_raw_stations(operator):
            feature = to_feature(raw_station, operator)
            if feature is None:
                skipped += 1
                continue
            features.append(feature)

    if skipped:
        print(f"Skipped {skipped} station record(s) missing coordinates.")

    ids = [f["properties"]["station_id"] for f in features]
    duplicates = {i for i in ids if ids.count(i) > 1}
    if duplicates:
        print(f"Warning: {len(duplicates)} duplicate station_id value(s) found: {duplicates}")

    return {"type": "FeatureCollection", "features": features}


def main() -> None:
    geojson = build_stations_geojson()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / "stations.geojson"
    out_path.write_text(json.dumps(geojson, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(geojson['features'])} stations -> {out_path}")


if __name__ == "__main__":
    main()
