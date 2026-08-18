# Workplan

Phased plan, roughly sequential. Each phase should leave the repo in a
working (if minimal) state — no long-lived broken branches.

## Phase 0 — Scaffolding (done)

- [x] Repo structure, README, docs (data sources, architecture)
- [x] Initial commit + public GitHub repo

## Phase 1 — Data acquisition (v1 scope: JR East + Tokyo Metro + Toei)

- [ ] Register ODPT API key; write `pipeline/ingest/odpt_stations.py` to
      pull station master data + coordinates for the three v1 operators,
      output raw JSON to `data/raw/odpt/`.
- [ ] Manually source 2-3 years of MLIT 混雑率 (congestion rate) releases
      (start with most recent + one pre-COVID year, e.g. 2023 and 2019, to
      make the COVID delta visible) into `data/raw/mlit/`.
- [ ] Manually source station ridership (乗車人員) pages/exports for the
      three v1 operators for the same years into `data/raw/ridership/`.
- [ ] Document exact source URLs and retrieval date for each raw file
      (append to `docs/DATA_SOURCES.md` per-file provenance notes).

**Exit criteria**: raw files for 2 operators-worth of station data + 2
years of congestion data sitting in `data/raw/`, each with a documented
source.

## Phase 2 — Normalization pipeline

- [ ] `pipeline/normalize/stations.py`: ODPT raw JSON → `stations.geojson`
- [ ] `pipeline/normalize/ridership.py`: per-operator raw files →
      `station_ridership.csv` (long format, normalized station IDs)
- [ ] `pipeline/normalize/congestion.py`: MLIT raw files →
      `line_congestion.csv`
- [ ] Station ID reconciliation — ODPT IDs vs. whatever key each operator's
      ridership export uses (likely station name matching with a manual
      override table for ambiguous/renamed stations). This is the fiddliest
      part; expect iteration.
- [ ] Basic validation: no orphan ridership rows without a matching
      station, no duplicate station IDs, sane value ranges.

**Exit criteria**: `data/processed/` populated and passing validation for
v1 scope; a notebook in `notebooks/` sanity-checking the joined data
(distribution of ridership, congestion rates by line, spot-check a few
well-known stations like Shinjuku/Ikebukuro against known figures).

## Phase 3 — Frontend MVP

- [ ] Vite + TS + MapLibre GL scaffold in `web/`
- [ ] Load enriched station GeoJSON, render stations as circle markers
      sized by ridership
- [ ] Color line segments by congestion rate (static, latest year only)
- [ ] Basic legend + station hover tooltip (name, operator, ridership,
      congestion if on a surveyed section)

**Exit criteria**: a static site running locally (`npm run dev`) showing a
usable, if unstyled, congestion map for v1-scope operators, single year.

## Phase 4 — Time dimension

- [ ] Year slider/selector wired to re-filter the loaded dataset
      client-side
- [ ] Visual treatment for year-over-year change (e.g. toggle or
      side-by-side comparison mode) — highlight the COVID-era dip if data
      supports it

**Exit criteria**: can scrub between at least 2 years and see the map
update.

## Phase 5 — Polish + expand coverage

- [ ] Deploy to GitHub Pages (or equivalent) with a CI step to rebuild on
      push
- [ ] Expand operator coverage beyond v1 scope (Tobu, Tokyu, Odakyu, Keio,
      Seibu, ...) — mostly repeating Phase 1/2 per new operator
- [ ] Visual polish pass (styling, mobile responsiveness, better legend)
- [ ] README screenshots/demo link

## Backlog / stretch ideas (not scoped yet)

- Search/filter by station or line name
- Transfer-station highlighting (stations serving multiple lines/operators)
- Export current view as an image
- Compare mode: two years side by side
