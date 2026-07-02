/*
  Milestone 0 placeholder script.

  Purpose: verify, at scaffold time, that the frontend container can reach
  the backend container's API over HTTP (through the browser, i.e. via the
  host-mapped port — not the internal Docker network name, since this code
  runs client-side).

  Real dashboard logic (api.js, charts.js, blockchain-explorer.js, Leaflet
  map integration) is out of scope until Milestone 7.
*/

const API_BASE_URL = "http://localhost:8000/api/v1";

async function checkApiStatus() {
  const statusEl = document.getElementById("api-status");
  try {
    const response = await fetch(`${API_BASE_URL}/system/health`);
    const body = await response.json();
    statusEl.textContent = body.data.status;
    statusEl.style.color = body.data.status === "ok" ? "#4ade80" : "#f87171";
  } catch (err) {
    statusEl.textContent = "unreachable";
    statusEl.style.color = "#f87171";
  }
}

checkApiStatus();
