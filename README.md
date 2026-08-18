# Station Congestion Heatmap

A visualization project mapping passenger congestion across Japan's rail
network (JR East, Tokyo Metro, Toei, Tobu, Tokyu, Odakyu, and other private
operators) using publicly available government and open transit data.

## Goal

Build an interactive map/heatmap showing:
- **Station-level congestion** — annual boarding/alighting passenger volume
  (乗降人員) by station, sourced from operator disclosures and MLIT stats.
- **Line-level peak congestion rate** (混雑率) — the well-known "% of seated
  capacity" figure MLIT publishes yearly for the most crowded sections of
  major commuter lines (e.g. Tozai Line, Denentoshi Line).
- **Trends over time** — a year slider to see how congestion has shifted
  (e.g. pre/post-COVID ridership drop and recovery).

This is a data visualization / analytics project, not a real-time crowding
tracker — the underlying data is published annually, not live.

## Status

Early scaffolding. See [WORKPLAN.md](WORKPLAN.md) for the phased plan and
[docs/DATA_SOURCES.md](docs/DATA_SOURCES.md) / [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
for data and design decisions made so far.

## Repository layout

```
data/
  raw/          # untouched downloaded source files (excel/csv), gitignored except samples
  processed/    # cleaned, normalized parquet/csv/sqlite outputs
pipeline/        # Python ingestion + normalization scripts
web/             # frontend map/visualization app
docs/            # data source notes, architecture decisions
notebooks/       # exploratory analysis
```

## Pipeline setup

```
python -m venv .venv
.venv/Scripts/activate        # .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
cp .env.example .env          # then fill in ODPT_API_KEY
```

Get a free ODPT API key at https://developer.odpt.org/ (register, create an
application, copy the consumer key into `.env`).

Fetch station master data for all v1 operators (JR East, Tokyo Metro, Toei):

```
python -m pipeline.ingest.odpt_stations --all
```

Output lands in `data/raw/odpt/` (gitignored — see `docs/DATA_SOURCES.md`
for provenance/licensing notes).

## Frontend

```
cd web
npm install
npm run dev
```

`npm run dev`/`npm run build` automatically copy the latest
`data/processed/stations.geojson` into `web/public/data/` first (via
`scripts/build-data.mjs`) — if the pipeline hasn't been run yet, it falls
back to an empty placeholder so the app still loads.

## License

MIT — see [LICENSE](LICENSE). Underlying datasets carry their own
licenses/terms; see [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md) for details.
