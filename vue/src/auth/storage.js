const TOKEN_KEY = 'warehouse_auth_token';
const HOUSEHOLD_KEY = 'warehouse_household_id';

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

