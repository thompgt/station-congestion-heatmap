// Mirrors the schema written by pipeline/normalize/stations.py.
// See docs/ARCHITECTURE.md "Data model" for the source of truth.

export interface StationProperties {
  station_id: string;
  name: string;
  operator: string;
  lines: string[];
  // Populated once pipeline/normalize/ridership.py has real data and the
  // build-data join step (Phase 4) merges it in.
  daily_boardings?: number;
}

export type StationFeature = GeoJSON.Feature<GeoJSON.Point, StationProperties>;
export type StationFeatureCollection = GeoJSON.FeatureCollection<GeoJSON.Point, StationProperties>;
