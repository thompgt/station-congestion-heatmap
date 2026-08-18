# Data Sources

This project relies entirely on publicly available data — there is no
real-time crowding API for Japanese rail at station granularity, so
"congestion" here means published annual statistics, not live sensor data.

## 1. MLIT 都市鉄道の混雑率調査結果 (Rail congestion rate survey)

- **Publisher**: Ministry of Land, Infrastructure, Transport and Tourism (MLIT)
- **What it is**: Annual survey of peak-hour congestion rate (混雑率, % of
  design capacity) for the single most crowded section of each major
  commuter line in major metro areas (Tokyo, Osaka, Nagoya, etc.).
- **Format**: Published as PDF/Excel press releases, usually yearly in
  summer/fall covering the prior fiscal year.
- **Access**: https://www.mlit.go.jp/ (search "混雑率" — URL changes per
  year's release, no stable API). Requires manual download + parsing per
  year; format has been fairly consistent (line name, operator, section,
  congestion %) but cell layout varies by year.
- **License**: Government statistics, generally reusable with attribution
  under Japan's standard government open data terms (要確認 per release).
- **Use in this project**: primary source for line-level congestion % time
  series.

## 2. Operator-published station passenger volume (乗降人員/乗車人員)

- **Publisher**: Individual operators — JR East, Tokyo Metro, Toei, Tobu,
  Tokyu, Odakyu, Keio, Seibu, etc. — each publish annual station-level
  boarding (and sometimes boarding+alighting) counts, typically as part of
  investor/corporate disclosure or "各駅の乗車人員" pages.
- **Format**: Varies wildly — HTML tables, PDF, Excel. No unified schema.
- **Access**: Per-operator corporate/investor relations sites. No
  aggregator API currently known; ODPT (below) does not carry ridership
  numbers.
- **Use in this project**: station-level marker sizing/coloring on the map.
  Because format is inconsistent, ingestion needs a per-operator parser
  (see `pipeline/` — one adapter module per operator, normalized to a
  common schema).

## 3. ODPT — Open Data Platform for Transportation in Japan

- **URL**: https://www.odpt.org/
- **What it is**: Aggregated open data platform covering static data
  (station master data, GTFS-JP-derived route/timetable info, station
  geo-coordinates) and some real-time operation info (train positions,
  delays) for participating operators (Tokyo Metro, Toei, JR East partial,
  Tobu, Tokyu, Odakyu, and others).
- **Access**: Free API key via developer registration
  (https://developer.odpt.org/). Rate-limited.
- **License**: CC BY 4.0 (per ODPT terms) — attribution required.
- **Use in this project**: station geo-coordinates and station/line master
  data (IDs, names, operator, line association) to join against the
  congestion and ridership datasets, and to plot stations on the map.

## 4. GTFS-JP feeds

- Some operators (Tobu, Odakyu, and others) publish GTFS-JP static feeds
  directly or via ODPT. Useful as a fallback for station coordinates/line
  topology if ODPT coverage is incomplete for a given operator.

## Open questions / TODO

- [ ] Confirm exact reusability terms for MLIT PDF/Excel congestion data
      (government data is generally CC BY-compatible in Japan but verify
      per release).
- [ ] Register for an ODPT API key.
- [ ] Decide how far back in years to backfill (COVID-era 2020-2022 numbers
      are a notable, interesting anomaly worth including).
- [ ] Scope which operators to cover in v1 (recommend starting with JR East
      + Tokyo Metro + Toei, since they have the best data availability, then
      expanding to Tobu/Tokyu/Odakyu/etc.).
