// Backend se baat karne ka ek hi jagah. Token localStorage mein save hota hai.
const TOKEN_KEY = "codeclash_token";

export function getToken() {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* private mode etc. */
  }
}

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

export async function api(path, { method = "GET", body } = {}) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`/api/v1${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    let msg = data.detail || `Request failed (${res.status})`;
    if (Array.isArray(msg)) msg = msg.map((d) => d.msg).join(", "); // pydantic validation errors
    throw new ApiError(res.status, msg);
  }
  return data;
}

export function wsUrl(token) {
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  return `${proto}://${window.location.host}/ws?token=${encodeURIComponent(token)}`;
}
