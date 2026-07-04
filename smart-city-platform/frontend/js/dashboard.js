/*
  Top-level orchestration: login/logout, tab switching, the Lamps table +
  detail/override/config forms (role-gated), the Alerts panel (role-gated
  acknowledge), and ~15s polling on whichever tab is active. This is the
  module entrypoint loaded by index.html's <script type="module">.
*/

import * as api from "./api.js";
import * as auth from "./auth.js";
import { initMap, renderLampMarkers } from "./map.js";
import { renderHistoryChart } from "./charts.js";
import { initBlockchainTab, refreshBlockchainTab } from "./blockchain-explorer.js";

const POLL_INTERVAL_MS = 15000;

let activeTab = "map";
let pollTimer = null;
let selectedLampId = null;

// --- Login / logout --------------------------------------------------

function showDashboard() {
  document.getElementById("login-view").hidden = true;
  document.getElementById("dashboard-view").hidden = false;

  const user = auth.getCurrentUser();
  document.getElementById("current-user").textContent = user
    ? `${user.username} (${user.role})`
    : "";

  initMap();
  initBlockchainTab();
  switchTab("map");
  startPolling();
}

function showLogin() {
  document.getElementById("dashboard-view").hidden = true;
  document.getElementById("login-view").hidden = false;
  stopPolling();
}

document.getElementById("login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const username = document.getElementById("login-username").value;
  const password = document.getElementById("login-password").value;
  const errorEl = document.getElementById("login-error");
  errorEl.hidden = true;

  try {
    await auth.login(username, password);
    showDashboard();
  } catch {
    errorEl.textContent = "Identifiants invalides";
    errorEl.hidden = false;
  }
});

document.getElementById("logout-button").addEventListener("click", () => {
  auth.logout();
  showLogin();
});

// --- Tabs -------------------------------------------------------------

function switchTab(tabName) {
  activeTab = tabName;
  for (const button of document.querySelectorAll(".tab-button")) {
    button.classList.toggle("active", button.dataset.tab === tabName);
  }
  for (const panel of document.querySelectorAll(".tab-panel")) {
    panel.classList.toggle("active", panel.id === `tab-${tabName}`);
  }
  refreshActiveTab();
}

for (const button of document.querySelectorAll(".tab-button")) {
  button.addEventListener("click", () => switchTab(button.dataset.tab));
}

function refreshActiveTab() {
  if (activeTab === "map") refreshMap();
  else if (activeTab === "lamps") refreshLampsTable();
  else if (activeTab === "alerts") refreshAlerts();
  else if (activeTab === "blockchain") refreshBlockchainTab();
}

function startPolling() {
  stopPolling();
  pollTimer = setInterval(refreshActiveTab, POLL_INTERVAL_MS);
}

function stopPolling() {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = null;
}

// --- Map ----------------------------------------------------------------

async function refreshMap() {
  try {
    const response = await api.listLamps();
    renderLampMarkers(response.data);
  } catch (err) {
    console.error("Failed to refresh map", err);
  }
}

// --- Lamps ----------------------------------------------------------------

async function refreshLampsTable() {
  const tbody = document.querySelector("#lamps-table tbody");
  try {
    const response = await api.listLamps();
    tbody.innerHTML = "";
    for (const lamp of response.data) {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${lamp.device_id}</td>
        <td class="status-${lamp.status}">${lamp.status}</td>
        <td>${lamp.current_brightness_pct.toFixed(1)}%</td>
        <td>${new Date(lamp.last_seen).toLocaleString()}</td>
      `;
      row.addEventListener("click", () => showLampDetail(lamp.device_id));
      tbody.appendChild(row);
    }
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="4">Erreur: ${err.message}</td></tr>`;
  }
}

async function showLampDetail(deviceId) {
  selectedLampId = deviceId;
  document.getElementById("lamp-detail").hidden = false;
  document.getElementById("lamp-detail-title").textContent = deviceId;

  const [lampResponse, historyResponse] = await Promise.all([
    api.getLamp(deviceId),
    api.getLampHistory(deviceId, 1, 50),
  ]);

  renderHistoryChart(document.getElementById("lamp-history-chart"), historyResponse.data);

  document.getElementById("override-form").hidden = !auth.hasRole("operator");

  const configForm = document.getElementById("config-form");
  configForm.hidden = !auth.hasRole("admin");
  if (!configForm.hidden) {
    const config = lampResponse.data.config;
    document.getElementById("config-min").value = config.min_brightness_pct;
    document.getElementById("config-max").value = config.max_brightness_pct;
    document.getElementById("config-timeout").value = config.offline_timeout_seconds;
    document.getElementById("config-tolerance").value = config.actuator_mismatch_tolerance_pct;
  }
}

document.getElementById("override-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!selectedLampId) return;

  const brightnessPct = parseFloat(document.getElementById("override-brightness").value);
  const reason = document.getElementById("override-reason").value;

  try {
    await api.overrideLamp(selectedLampId, brightnessPct, reason);
    await showLampDetail(selectedLampId);
    refreshLampsTable();
  } catch (err) {
    window.alert(`Erreur: ${err.message}`);
  }
});

document.getElementById("config-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!selectedLampId) return;

  const config = {
    min_brightness_pct: parseFloat(document.getElementById("config-min").value),
    max_brightness_pct: parseFloat(document.getElementById("config-max").value),
    offline_timeout_seconds: parseInt(document.getElementById("config-timeout").value, 10),
    actuator_mismatch_tolerance_pct: parseFloat(
      document.getElementById("config-tolerance").value
    ),
  };

  try {
    await api.updateLampConfig(selectedLampId, config);
    await showLampDetail(selectedLampId);
  } catch (err) {
    window.alert(`Erreur: ${err.message}`);
  }
});

// --- Alerts ----------------------------------------------------------------

document.getElementById("alerts-filter-resolved").addEventListener("change", refreshAlerts);

async function refreshAlerts() {
  const list = document.getElementById("alerts-list");
  const resolvedFilter = document.getElementById("alerts-filter-resolved").value;

  try {
    const response = await api.listAlerts({ resolved: resolvedFilter });
    list.innerHTML = "";

    for (const anomaly of response.data) {
      const item = document.createElement("li");
      item.className = `alert-card severity-${anomaly.severity} ${anomaly.resolved ? "resolved" : ""}`;
      item.innerHTML = `
        <div>
          <strong>${anomaly.type}</strong> — ${anomaly.device_id}
          <div class="alert-meta">
            ${new Date(anomaly.detected_at).toLocaleString()} · sévérité ${anomaly.severity}
          </div>
        </div>
      `;

      if (!anomaly.resolved && auth.hasRole("operator")) {
        const button = document.createElement("button");
        button.textContent = "Acquitter";
        button.addEventListener("click", async () => {
          try {
            await api.acknowledgeAlert(anomaly.id);
            refreshAlerts();
          } catch (err) {
            window.alert(`Erreur: ${err.message}`);
          }
        });
        item.appendChild(button);
      }

      list.appendChild(item);
    }
  } catch (err) {
    list.innerHTML = `<li>Erreur: ${err.message}</li>`;
  }
}

// --- Boot -------------------------------------------------------------

if (auth.isAuthenticated()) {
  showDashboard();
} else {
  showLogin();
}
