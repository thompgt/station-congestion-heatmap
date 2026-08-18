import * as maplibregl from "maplibre-gl";
import type { StationFeatureCollection } from "./types";

// Free/open demo style — no API key required. Swap for a self-hosted or
// preferred style later (see WORKPLAN.md Phase 5.3 polish pass).
const BASE_STYLE = "https://demotiles.maplibre.org/style.json";

// Roughly centers on central Tokyo.
const INITIAL_CENTER: [number, number] = [139.7, 35.68];
const INITIAL_ZOOM = 10.5;

export function createMap(container: HTMLElement): maplibregl.Map {
  return new maplibregl.Map({
    container,
    style: BASE_STYLE,
    center: INITIAL_CENTER,
    zoom: INITIAL_ZOOM,
  });
}

export function addStationLayer(map: maplibregl.Map, data: StationFeatureCollection): void {
  map.addSource("stations", { type: "geojson", data });

  map.addLayer({
    id: "stations-circle",
    type: "circle",
    source: "stations",
    paint: {
      // Placeholder fixed radius/color until daily_boardings is populated
      // by the pipeline (Phase 4) — swap for a data-driven expression
      // once that field is reliably present, e.g.:
      //   "circle-radius": ["interpolate", ["linear"], ["get", "daily_boardings"], 0, 3, 500000, 24]
      "circle-radius": 5,
      "circle-color": "#2563eb",
      "circle-stroke-width": 1,
      "circle-stroke-color": "#ffffff",
    },
  });

  const popup = new maplibregl.Popup({ closeButton: false, closeOnClick: false });

  map.on("mouseenter", "stations-circle", (e: maplibregl.MapLayerMouseEvent) => {
    map.getCanvas().style.cursor = "pointer";
    const feature = e.features?.[0];
    if (!feature) return;
    const props = feature.properties as Record<string, unknown>;
    const coordinates = (feature.geometry as GeoJSON.Point).coordinates.slice() as [number, number];
    popup
      .setLngLat(coordinates)
      .setHTML(`<strong>${props.name}</strong><br/>${props.operator}`)
      .addTo(map);
  });

  map.on("mouseleave", "stations-circle", () => {
    map.getCanvas().style.cursor = "";
    popup.remove();
  });
}
