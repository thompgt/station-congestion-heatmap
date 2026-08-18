// Copies pipeline output (data/processed/) into web/public/data/ so the
// frontend can fetch it as static assets. Run automatically before
// `npm run dev` / `npm run build` (see package.json "predev"/"prebuild").
//
// This is deliberately a plain copy for now (Phase 3 MVP: latest-year
// station data only). Phase 4 replaces this with a real join step that
// merges stations.geojson + station_ridership.csv + line_congestion.csv
// into one enriched GeoJSON keyed by year — see WORKPLAN.md Phase 3.1/4.

import { existsSync, mkdirSync, copyFileSync, writeFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PROCESSED_DIR = join(__dirname, "..", "..", "data", "processed");
const OUT_DIR = join(__dirname, "..", "public", "data");

mkdirSync(OUT_DIR, { recursive: true });

const stationsSrc = join(PROCESSED_DIR, "stations.geojson");
const stationsOut = join(OUT_DIR, "stations.geojson");

if (existsSync(stationsSrc)) {
  copyFileSync(stationsSrc, stationsOut);
  console.log(`Copied ${stationsSrc} -> ${stationsOut}`);
} else {
  // No pipeline output yet — write an empty FeatureCollection so the
  // frontend has something valid to fetch instead of a 404 during
  // early development (see src/main.ts status handling).
  writeFileSync(stationsOut, JSON.stringify({ type: "FeatureCollection", features: [] }, null, 2));
  console.log(
    `No processed data found at ${stationsSrc} yet — wrote empty placeholder to ${stationsOut}. ` +
      "Run the pipeline (see README.md) to populate real data."
  );
}
