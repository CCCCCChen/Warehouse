const TOKEN_KEY = 'warehouse_auth_token';
const HOUSEHOLD_KEY = 'warehouse_household_id';
const SESSIONS_KEY = 'warehouse_sessions_v1';

export function getAuthToken() {
  return localStorage.getItem(TOKEN_KEY) || '';
}

export function setAuthToken(token) {
  if (!token) {
    localStorage.removeItem(TOKEN_KEY);
  } else {
    localStorage.setItem(TOKEN_KEY, token);
  }
}

export function getHouseholdId() {
  return localStorage.getItem(HOUSEHOLD_KEY) || '';
}

export function setHouseholdId(householdId) {
  if (!householdId) {
    localStorage.removeItem(HOUSEHOLD_KEY);
  } else {
    localStorage.setItem(HOUSEHOLD_KEY, householdId);
  }
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(HOUSEHOLD_KEY);
}

function safeParseJson(text, fallback) {
  try {
    return JSON.parse(text);
  } catch (e) {
    return fallback;
  }
}

export function getSessions() {
  const raw = localStorage.getItem(SESSIONS_KEY);
  const list = raw ? safeParseJson(raw, []) : [];
  return Array.isArray(list) ? list : [];
}

export function saveSessions(sessions) {
  localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions || []));
}

export function upsertSession(session) {
  const sessions = getSessions();
  const idx = sessions.findIndex(s => s && s.household_id === session.household_id);
  const next = { ...session, updated_at: Date.now() };
  if (idx >= 0) {
    sessions.splice(idx, 1, { ...sessions[idx], ...next });
  } else {
    sessions.unshift(next);
  }
  saveSessions(sessions);
  return sessions;
}

export function removeSession(householdId) {
  const sessions = getSessions().filter(s => s && s.household_id !== householdId);
  saveSessions(sessions);
  if (getHouseholdId() === householdId) {
    clearAuth();
  }
  return sessions;
}

export function setCurrentSession(householdId, token) {
  setHouseholdId(householdId);
  setAuthToken(token);
}

export function clearAllSessions() {
  clearAuth();
  localStorage.removeItem(SESSIONS_KEY);
}
