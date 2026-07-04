/*
  Leaflet map: one marker per lamp with a non-null `location` (see
  backend/app/domain/entities/location.py -- only seeded lamps have one,
  auto-created ones from telemetry ingestion don't).

  `L` is the Leaflet global loaded via <script> in index.html before this
  module -- module scripts still share the page's global `window`.
*/

const TUNIS_CENTER = [36.8065, 10.1815];

let map = null;
const markersByDeviceId = new Map();

export function initMap() {
  if (map) return map;

  map = L.map("map").setView(TUNIS_CENTER, 13);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);

  return map;
}

function markerColor(status) {
  return status === "online" ? "#4ade80" : "#f87171";
}

function popupHtml(lamp) {
  const lastSeen = new Date(lamp.last_seen).toLocaleString();
  return `
    <strong>${lamp.device_id}</strong><br />
    ${lamp.location?.label ?? ""}<br />
    Statut : ${lamp.status}<br />
    Luminosité : ${lamp.current_brightness_pct.toFixed(1)}%<br />
    Dernière vue : ${lastSeen}
  `;
}

export function renderLampMarkers(lamps) {
  if (!map) return;

  const seenDeviceIds = new Set();

  for (const lamp of lamps) {
    if (!lamp.location) continue;
    seenDeviceIds.add(lamp.device_id);

    const color = markerColor(lamp.status);
    const existing = markersByDeviceId.get(lamp.device_id);

    if (existing) {
      existing.setLatLng([lamp.location.lat, lamp.location.lng]);
      existing.setPopupContent(popupHtml(lamp));
      existing.setStyle({ color, fillColor: color });
    } else {
      const marker = L.circleMarker([lamp.location.lat, lamp.location.lng], {
        radius: 10,
        color,
        fillColor: color,
        fillOpacity: 0.8,
      }).addTo(map);
      marker.bindPopup(popupHtml(lamp));
      markersByDeviceId.set(lamp.device_id, marker);
    }
  }

  for (const [deviceId, marker] of markersByDeviceId) {
    if (!seenDeviceIds.has(deviceId)) {
      map.removeLayer(marker);
      markersByDeviceId.delete(deviceId);
    }
  }
}
