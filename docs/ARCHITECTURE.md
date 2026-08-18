# Architecture

## Overview

Three stages: **ingest → normalize/store → visualize**. No live/real-time
component — data refresh is a periodic (yearly) manual/scripted pipeline
run, not a running service.

```
[operator sites / MLIT releases / ODPT API]
        |  (per-source adapter, pipeline/ingest/*.py)
        v
   data/raw/                (untouched source files, mostly gitignored)
        |  (pipeline/normalize/*.py)
        v
   data/processed/          (station_ridership.parquet, line_congestion.parquet, stations.geojson)
        |
        v
   web/  (static frontend, reads processed data directly — no backend server)
```

## Why no backend server

Data updates ~yearly, dataset size is small (a few thousand stations x a
handful of years), and there's no auth/user-generated content. A static
frontend reading pre-built JSON/GeoJSON/Parquet-derived files avoids
running and hosting a server, and lets the whole thing be deployed as a
static site (e.g. GitHub Pages). Revisit this only if the project grows a
feature that needs a live backend (e.g. user accounts, write access).

## Stack

- **Pipeline**: Python. `pandas` for tabular normalization,
  `openpyxl`/`pdfplumber` for parsing Excel/PDF source releases, `httpx`
  for ODPT API calls. Output committed as versioned files in
  `data/processed/` (Parquet for tabular, GeoJSON for station geometry) so
  the frontend has no runtime dependency on the pipeline.
- **Frontend**: Vite + TypeScript + a mapping library
  (MapLibre GL JS, since it's open-source/no API-key-cost, vs. Mapbox GL).
  Heatmap/circle layers driven directly from the GeoJSON station data,
  colored/sized by the selected year's congestion metric. A year slider
  re-filters the rendered layer client-side (no requests needed once data
  is loaded).
- **Hosting**: GitHub Pages (or Vercel/Netlify free tier) serving the
  built `web/` static site.

## Data model (draft)

`stations.geojson` — one Feature per station:
```json
{
  "type": "Feature",
  "geometry": { "type": "Point", "coordinates": [lon, lat] },
  "properties": {
    "station_id": "odpt.Station:...",
    "name": "Shinjuku",
    "operator": "JR-East",
    "lines": ["JR-East.Chuo", "JR-East.Yamanote"]
  }
}
```

`station_ridership.parquet` — long format, one row per station/year:
| station_id | year | daily_boardings |
|---|---|---|

`line_congestion.parquet` — one row per line/year (MLIT survey):
| operator | line | section | year | congestion_rate_pct |
|---|---|---|---|---|

Frontend joins ridership/congestion onto station geometry by
`station_id`/line name at build time or load time (TBD — likely a small
build-step join into a single enriched GeoJSON to keep the frontend dumb).

## Open design questions

- [ ] Parquet vs. plain CSV/JSON for `data/processed/` — Parquet is more
      efficient but adds a read dependency for anyone poking at the data
      casually. Leaning CSV/GeoJSON for accessibility given small data size.
- [ ] Whether line-level congestion (a single number per line-section)
      should render as a colored line segment on the map vs. only
      station-level markers use the heatmap treatment. Likely both: line
      color = congestion rate, station marker size = ridership volume.
- [ ] Client-side only vs. small prebuild step (Node script) to join
      datasets into one file — leaning prebuild step for simplicity of the
      deployed frontend.
