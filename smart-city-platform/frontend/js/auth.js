/*
  JWT storage + client-side role gating.

  Decoding the JWT payload here is UI-only convenience (hide/disable
  write actions below the required role) -- the backend independently
  re-validates and enforces the real role check on every request (see
  backend/app/security/rbac.py's require_role). Nothing here is a
  security boundary.
*/

import * as api from "./api.js";

const TOKEN_KEY = "access_token";

const ROLE_RANK = { viewer: 0, operator: 1, admin: 2 };

function decodeJwtPayload(token) {
  const payloadSegment = token.split(".")[1];
  const normalized = payloadSegment.replace(/-/g, "+").replace(/_/g, "/");
  return JSON.parse(atob(normalized));
}

export function isAuthenticated() {
  return Boolean(localStorage.getItem(TOKEN_KEY));
}

export function getCurrentUser() {
  const token = localStorage.getItem(TOKEN_KEY);
  if (!token) return null;
  try {
    const payload = decodeJwtPayload(token);
    return { username: payload.sub, role: payload.role };
  } catch {
    return null;
  }
}

export function hasRole(minimumRole) {
  const user = getCurrentUser();
  if (!user || !(minimumRole in ROLE_RANK)) return false;
  return ROLE_RANK[user.role] >= ROLE_RANK[minimumRole];
}

export async function login(username, password) {
  const response = await api.login(username, password);
  localStorage.setItem(TOKEN_KEY, response.data.access_token);
}

export function logout() {
  localStorage.removeItem(TOKEN_KEY);
}
