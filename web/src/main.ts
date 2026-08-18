import "./style.css";
import { createMap, addStationLayer } from "./map";
import type { StationFeatureCollection } from "./types";

const statusEl = document.querySelector<HTMLParagraphElement>("#status")!;
const mapContainer = document.querySelector<HTMLDivElement>("#map")!;

async function loadStations(): Promise<StationFeatureCollection> {
  const response = await fetch("/data/stations.geojson");
  if (!response.ok) {
    throw new Error(`Failed to load stations.geojson: ${response.status}`);
  }
  return response.json();
}

async function main(): Promise<void> {
  const map = createMap(mapContainer);

  map.on("load", async () => {
    try {
      const stations = await loadStations();
      addStationLayer(map, stations);

      if (stations.features.length === 0) {
        statusEl.textContent =
          "No station data yet — run the pipeline (see README.md) to populate the map.";
      } else {
        statusEl.textContent = `${stations.features.length} stations loaded.`;
      }
    } catch (err) {
      console.error(err);
      statusEl.textContent = "Failed to load station data — see console for details.";
    }
  });
}

main();
