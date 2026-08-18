# Workplan

Detailed, phased plan. Each phase should leave the repo in a working (if
minimal) state — no long-lived broken branches. Tasks are written at a
level of detail meant to be picked up directly (file paths, function
names, acceptance criteria) rather than re-derived later.

**v1 scope** (operators): JR East, Tokyo Metro, Toei. Chosen because they
have the most consistent, best-documented open data (ODPT coverage +
regular ridership disclosures). Everything after Phase 5 generalizes the
pipeline to add more operators.

**v1 scope** (years): 2019 (pre-COVID baseline) and the most recent
available year at time of ingestion (currently 2023 or 2024 depending on
release timing) — chosen specifically to make the COVID ridership collapse
and recovery visible, which is the most interesting trend in this dataset.

---

## Phase 0 — Scaffolding (done)

- [x] Repo structure, README, docs (data sources, architecture)
- [x] Initial commit + public GitHub repo

---

## Phase 1 — Data acquisition

### 1.1 ODPT access

- [ ] Register a developer account at https://developer.odpt.org/ and
      obtain an API "consumer key".
- [ ] Store the key locally in `.env` (gitignored) as `ODPT_API_KEY=...`;
      add `.env.example` with the empty var name documented so future
      setup doesn't require re-discovering this.
- [ ] Confirm via a manual `curl`/`httpx` call that the key works against
      the `odpt:Station` endpoint for at least one JR East station before
      writing any pipeline code.

### 1.2 Station master data ingestion

- [ ] `pipeline/ingest/odpt_stations.py`
  - Function `fetch_stations(operator: str) -> list[dict]` — calls ODPT
    `odpt:Station` endpoint filtered by `odpt:operator`, paginating if
    needed.
  - Called once per v1 operator (`odpt.Operator:JR-East`,
    `odpt.Operator:TokyoMetro`, `odpt.Operator:Toei`).
  - Writes raw JSON response to `data/raw/odpt/stations_<operator>.json`
    (one file per operator, untouched API response — no transformation
    here, that's Phase 2).
  - CLI entry point: `python -m pipeline.ingest.odpt_stations --operator
    JR-East` (and a `--all` flag to loop v1 operators).
- [ ] Spot-check output: confirm Shinjuku, Ikebukuro, and Otemachi appear
      with plausible lat/lon (Tokyo bounding box roughly lat 35.5-35.9,
      lon 139.5-139.9).

### 1.3 MLIT congestion rate data

- [ ] Locate and download the MLIT 都市鉄道の混雑率調査結果 press release
      for the two target years (2019, latest). These are typically PDF or
      Excel attachments linked from MLIT's press release archive
      (search 国土交通省 混雑率 調査結果 <year>).
- [ ] Save raw files as `data/raw/mlit/congestion_2019.xlsx` (or `.pdf`)
      and `data/raw/mlit/congestion_<latest_year>.xlsx`.
- [ ] Record in `docs/DATA_SOURCES.md` (append to a new "Provenance log"
      section): exact URL, retrieval date, and which file it maps to.
- [ ] If only PDF is available for a given year, note that in
      `docs/DATA_SOURCES.md` — Phase 2 parsing will need `pdfplumber`
      table extraction instead of `openpyxl`, which is less reliable and
      may need manual correction of a few rows.

### 1.4 Station ridership data (per operator)

- [ ] JR East: locate annual "各駅の乗車人員" data (usually a page or
      downloadable table on JR East's corporate/investor site). Save as
      `data/raw/ridership/jr_east_<year>.<ext>` for each target year.
- [ ] Tokyo Metro: same, from Tokyo Metro's corporate site (乗降人員).
      `data/raw/ridership/tokyo_metro_<year>.<ext>`.
- [ ] Toei: same, from Toei Subway's site. `data/raw/ridership/toei_<year>.<ext>`.
- [ ] For each, record source URL + retrieval date in
      `docs/DATA_SOURCES.md` provenance log. Note the exact column meaning
      (boarding only vs. boarding+alighting — these are NOT the same
      metric and mixing them across operators would corrupt comparisons;
      if operators differ, note the discrepancy explicitly and decide in
      Phase 2 whether to normalize or keep operator-specific metrics with
      a `metric_type` column).

### 1.5 Provenance logging

- [ ] Add a "Provenance log" section to `docs/DATA_SOURCES.md` — a table
      with columns: `file | source URL | retrieved date | notes`. Fill in
      one row per raw file downloaded in 1.2-1.4. This is the thing that
      makes the dataset reproducible/auditable later; don't skip it even
      though it feels like overhead now.

**Exit criteria**: `data/raw/odpt/`, `data/raw/mlit/`, and
`data/raw/ridership/` each populated for all v1 operators/years, every
file logged in the provenance table. Nothing parsed yet.

**Risks / known unknowns**:
- MLIT file format changes year to year (column order, units) — expect to
  hand-inspect each file before writing a generic parser.
- Ridership metric definitions may not be directly comparable across
  operators (see 1.4) — resolve before Phase 2 normalization, not during.

---

## Phase 2 — Normalization pipeline

### 2.1 Station normalization

- [ ] `pipeline/normalize/stations.py`
  - `load_raw_stations(operator: str) -> list[dict]` reads
    `data/raw/odpt/stations_<operator>.json`.
  - `to_feature(station: dict) -> geojson Feature` maps ODPT fields to the
    schema in `docs/ARCHITECTURE.md` (`station_id`, `name`, `operator`,
    `lines`).
  - `main()` loops all v1 operators, dedupes stations that appear under
    multiple operators' station lists (e.g. a Tokyo Metro/Toei
    interchange station may be listed by both — decide whether to keep as
    separate features per operator or merge; recommend keeping separate
    features since fare gates/ridership are often counted per-operator,
    and note the decision in `docs/ARCHITECTURE.md`).
  - Writes `data/processed/stations.geojson`.
- [ ] Validation script check (can live in the same module behind
      `if __name__ == "__main__"` or a small `pipeline/validate.py`):
      every feature has non-null coordinates within the Tokyo bounding box,
      no duplicate `station_id`.

### 2.2 Ridership normalization

- [ ] `pipeline/normalize/ridership.py`
  - One small per-operator parser function since raw formats differ:
    `parse_jr_east(path) -> DataFrame`, `parse_tokyo_metro(path) ->
    DataFrame`, `parse_toei(path) -> DataFrame`, each returning columns
    `[station_name_raw, year, daily_boardings, metric_type]`.
  - `reconcile_station_id(station_name_raw, operator) -> station_id`:
    joins against `stations.geojson` by name. Expect mismatches (e.g.
    "新宿" vs "新宿駅", or stations renamed between years) — build a
    manual override table `pipeline/normalize/station_name_overrides.csv`
    (`raw_name,operator,station_id`) to patch unmatched rows rather than
    fuzzy-matching silently (fuzzy matching station names is a good way to
    quietly join the wrong station).
  - `main()` combines all operators/years into one long-format table,
    writes `data/processed/station_ridership.csv` with columns
    `station_id, year, daily_boardings, metric_type, operator`.
- [ ] Print/log any raw rows that failed to reconcile to a station_id
      (don't silently drop them) — add unresolved names to the override
      CSV until the unmatched count is zero or explicitly accepted as
      out-of-scope (e.g. a station outside the v1 operator set that
      happens to appear in a shared listing).

### 2.3 Congestion normalization

- [ ] `pipeline/normalize/congestion.py`
  - Parse each `data/raw/mlit/congestion_<year>.xlsx` (or PDF via
    `pdfplumber` table extraction) into rows of
    `[operator, line, section, year, congestion_rate_pct]`.
  - MLIT line/operator naming won't match ODPT naming exactly — build a
    second override/mapping table
    `pipeline/normalize/line_name_overrides.csv` (`mlit_operator,
    mlit_line, odpt_line_id`) as needed, same rationale as 2.2.
  - Writes `data/processed/line_congestion.csv`.

### 2.4 Validation + sanity notebook

- [ ] `notebooks/01_sanity_check.ipynb`:
  - Load all three processed files.
  - Assert no orphan `station_id` in ridership/congestion that's absent
    from `stations.geojson`.
  - Assert ridership/congestion values fall in plausible ranges (e.g.
    daily boardings roughly 100 to 800,000 — Shinjuku is the real-world
    upper bound; congestion rate roughly 50% to 250%).
  - Spot-check known values: Shinjuku ridership, and at least one
    well-known congested line (e.g. Tozai Line or Denentoshi Line) against
    a manually looked-up published figure, to catch unit/scale errors
    (e.g. accidentally parsing thousands as raw counts).
  - Plot a quick histogram of ridership and congestion distributions —
    mostly to eyeball for obviously-wrong outliers (a parsing bug showing
    up as one station with 50 million riders, etc).

**Exit criteria**: `data/processed/{stations.geojson,
station_ridership.csv, line_congestion.csv}` populated for v1 scope,
zero unresolved station/line name mismatches (or explicitly documented
exceptions), sanity notebook run with no failed assertions and spot-checks
matching known real-world figures within a reasonable margin.

**Risks / known unknowns**:
- Station name reconciliation is very likely the most time-consuming part
  of this whole project — budget for it accordingly, don't assume a naive
  string match will get more than ~80% on the first pass.
- PDF table extraction (if any MLIT year lacks an Excel version) may need
  manual row correction — treat `pdfplumber` output as a draft, not
  ground truth.

---

## Phase 3 — Frontend MVP

### 3.1 Scaffold

- [ ] `web/`: `npm create vite@latest . -- --template vanilla-ts` (or
      React if interactivity in later phases benefits from component
      state — lean toward plain TS + MapLibre first since the map *is*
      the app; add React only if UI complexity grows enough to justify
      it).
- [ ] Add `maplibre-gl` dependency.
- [ ] `web/src/data/` — build-time copy or symlink of
      `data/processed/*.{geojson,csv}` into the frontend's public assets
      (decide: Vite `public/` static copy vs. a small prebuild script that
      joins ridership+congestion into one enriched GeoJSON — architecture
      doc leans toward the prebuild-join approach, implement as
      `web/scripts/build-data.ts` run via a `predev`/`prebuild` npm
      script).

### 3.2 Base map + station layer

- [ ] `web/src/main.ts`: initialize MapLibre map centered on Tokyo
      (roughly `[139.7, 35.68]`, zoom ~11), using a free/open basemap
      style (e.g. MapLibre demo style or OSM raster tiles — avoid
      anything requiring a paid API key).
- [ ] Add enriched station GeoJSON as a source; render as a `circle` layer
      with `circle-radius` scaled by `daily_boardings` (latest year only
      for this phase) and `circle-color` on a fixed scale for now.

### 3.3 Line congestion layer

- [ ] Source line-section geometry — ODPT provides `odpt:Railway` geometry
      per line; join `line_congestion.csv` congestion rate onto matching
      line features by the `odpt_line_id` mapping built in 2.3.
- [ ] Render as a `line` layer colored on a sequential scale (e.g. green →
      yellow → red) by `congestion_rate_pct`, latest year only.

### 3.4 Legend + tooltip

- [ ] Static legend (color scale for congestion %, size scale for
      ridership) as a simple HTML overlay, not a map layer.
- [ ] Hover/click popup on station: name, operator, daily boardings, and
      (if applicable) the congestion rate of its highest-congestion
      connecting line-section.

**Exit criteria**: `npm run dev` in `web/` shows a working, if unstyled,
map of v1-scope stations sized by ridership and lines colored by
congestion, single (latest) year, with working hover tooltips.

---

## Phase 4 — Time dimension

- [ ] Rebuild `web/scripts/build-data.ts` output to include both target
      years (2019 + latest) per station/line rather than latest-only, keyed
      by year.
- [ ] Add a year slider/toggle UI element (`web/src/ui/YearControl.ts` or
      equivalent) that updates the MapLibre layer's data-driven styling
      expressions (`['get', ['concat', 'boardings_', year]]`-style
      property lookup, or swap the active GeoJSON source per year —
      evaluate both against MapLibre's expression capabilities before
      committing to one).
- [ ] Add a visual "change" mode: instead of absolute value per year, an
      optional toggle showing % change 2019 → latest, to make the
      COVID-era ridership drop/recovery visually obvious (this is
      arguably the single most interesting insight the dataset can show —
      worth getting right).

**Exit criteria**: user can toggle between 2019 and latest year (and,
ideally, a computed "change" view) and see the map update accordingly.

---

## Phase 5 — Deploy + expand coverage

### 5.1 Deployment

- [ ] Add GitHub Actions workflow `.github/workflows/deploy.yml`: on push
      to `main`, build `web/` (`npm ci && npm run build`) and publish
      `web/dist` to GitHub Pages (via `actions/deploy-pages` or
      `peaceiris/actions-gh-pages`).
- [ ] Enable GitHub Pages on the repo (Settings → Pages → source: GitHub
      Actions).
- [ ] Confirm the deployed site loads correctly (data assets resolve at
      the Pages base path, not just locally).

### 5.2 Expand operator coverage

Repeat Phase 1 (1.2-1.4) + Phase 2 (2.1-2.3) per new operator. Order by
data availability/interest:
- [ ] Tobu
- [ ] Tokyu
- [ ] Odakyu
- [ ] Keio
- [ ] Seibu
- [ ] Keisei / Keikyu (lower priority — smaller network footprint in the
      core Tokyo area this project focuses on)

For each: confirm ODPT has station coverage before starting (some smaller
operators may not be in ODPT's participant list — check
https://developer.odpt.org/ operator list first to avoid wasted effort).

### 5.3 Polish

- [ ] Visual/styling pass — consistent color palette, responsive layout
      for mobile viewport, loading state while data fetches.
- [ ] README: add a screenshot and the live Pages demo link.
- [ ] `docs/ARCHITECTURE.md`: update with any decisions that changed
      during implementation (expected — this doc should track reality,
      not the original guess).

**Exit criteria**: live public demo URL in the README, all six additional
operators present on the map (or explicitly deferred with a note if ODPT
coverage turns out to be missing for one).

---

## Backlog / stretch ideas (not scoped, revisit after Phase 5)

- Search/filter by station or line name.
- Transfer-station highlighting (stations serving multiple
  lines/operators) — visually distinct marker.
- Export current map view as an image.
- Side-by-side (rather than toggle) two-year comparison mode.
- Extend beyond Tokyo to Osaka/Nagoya metro areas (MLIT's congestion
  survey covers those too) — would need separate station/ridership
  sourcing per region; scope as its own phase if pursued, not a quick
  add-on.
- Real per-car crowding (not just line-average) — MLIT/some operators
  publish more granular data in places; investigate if v1 proves out.
