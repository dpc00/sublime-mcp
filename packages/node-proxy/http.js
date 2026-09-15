// PROOF: F5 — 2026-08-17. Per-endpoint HTTP timeouts. Quick reads stay at
// 10s so a hung backend fails fast; batch / install / search / find /
// eval_python_latest / run_build get 120s because those can legitimately
// exceed 10s while Sublime is still working.

const port = process.platform === 'win32' ? 9500 : 9501;
export const BASE = process.env.SUBLIME_MCP_BASE ?? `http://127.0.0.1:${port}`;

// Only sent when set -- matches the server's auth_token setting (unset by
// default on both sides, so this is a no-op unless the user opted in).
const AUTH_HEADERS = process.env.SUBLIME_MCP_TOKEN
  ? { Authorization: `Bearer ${process.env.SUBLIME_MCP_TOKEN}` }
  : {};

export const DEFAULT_TIMEOUT_MS = 10_000;
export const SLOW_TIMEOUT_MS = 120_000;
export const SLOW_ENDPOINTS = new Set([
  '/batch',
  '/install_package',
  '/search_packages',
  '/find_in_files',
  '/project_search',
  '/eval_python_latest',
  '/run_build',
]);

export function timeoutMsFor(endpoint) {
  return SLOW_ENDPOINTS.has(endpoint) ? SLOW_TIMEOUT_MS : DEFAULT_TIMEOUT_MS;
}

export async function get(endpoint, params = {}) {
  const url = new URL(endpoint, BASE);
  for (const [k, v] of Object.entries(params)) {
    url.searchParams.set(k, String(v));
  }
  const r = await fetch(url, {
    headers: AUTH_HEADERS,
    signal: AbortSignal.timeout(timeoutMsFor(endpoint)),
  });
  if (!r.ok) throw new Error(`HTTP ${r.status} from ${endpoint}`);
  return r.json();
}

export async function post(endpoint, body = {}) {
  const r = await fetch(new URL(endpoint, BASE), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...AUTH_HEADERS },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(timeoutMsFor(endpoint)),
  });
  if (!r.ok) throw new Error(`HTTP ${r.status} from ${endpoint}`);
  return r.json();
}
