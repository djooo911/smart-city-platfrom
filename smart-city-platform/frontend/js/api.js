/*
  Thin fetch wrapper around the backend REST API.

  API_BASE_URL defaults to the live Render deployment -- same
  demo-reliability reasoning as the Milestone 5 ESP32 firmware's hardcoded
  backend URL (avoids local docker-compose networking assumptions when
  just opening this page in a browser). For local development against
  `docker-compose up`, change it to "http://localhost:8000/api/v1".
*/

export const API_BASE_URL = "https://smart-city-platfrom.onrender.com/api/v1";

const TOKEN_KEY = "access_token";

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function request(method, path, { body, auth = true } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth) {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  const payload = await response.json().catch(() => null);

  if (!response.ok) {
    const message = payload?.detail || payload?.error?.message || `HTTP ${response.status}`;
    throw new ApiError(message, response.status);
  }

  return payload;
}

export function login(username, password) {
  return request("POST", "/auth/login", { body: { username, password }, auth: false });
}

export function listLamps() {
  return request("GET", "/lamps");
}

export function getLamp(deviceId) {
  return request("GET", `/lamps/${encodeURIComponent(deviceId)}`);
}

export function getLampHistory(deviceId, page = 1, pageSize = 20) {
  return request(
    "GET",
    `/lamps/${encodeURIComponent(deviceId)}/history?page=${page}&page_size=${pageSize}`
  );
}

export function overrideLamp(deviceId, brightnessPct, reason) {
  return request("POST", `/lamps/${encodeURIComponent(deviceId)}/override`, {
    body: { brightness_pct: brightnessPct, reason },
  });
}

export function updateLampConfig(deviceId, config) {
  return request("PATCH", `/lamps/${encodeURIComponent(deviceId)}/config`, { body: config });
}

export function listAlerts({ deviceId, resolved, severity } = {}) {
  const params = new URLSearchParams();
  if (deviceId) params.set("device_id", deviceId);
  if (resolved !== undefined && resolved !== "") params.set("resolved", resolved);
  if (severity) params.set("severity", severity);
  const query = params.toString();
  return request("GET", `/alerts${query ? `?${query}` : ""}`);
}

export function acknowledgeAlert(alertId) {
  return request("POST", `/alerts/${encodeURIComponent(alertId)}/acknowledge`);
}

export function listBlocks(page = 1, pageSize = 20) {
  return request("GET", `/blockchain/blocks?page=${page}&page_size=${pageSize}`);
}

export function getBlock(index) {
  return request("GET", `/blockchain/blocks/${index}`);
}

export function verifyChain() {
  return request("GET", "/blockchain/verify");
}

export function listBlockchainEvents(deviceId) {
  return request("GET", `/blockchain/events?device_id=${encodeURIComponent(deviceId)}`);
}
