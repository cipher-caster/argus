/**
 * Centralized API client for Argus
 *
 * Single source of truth for API_URL and a typed fetch wrapper.
 * All API modules (api.ts, marketApi.ts, indicatorApi.ts) must
 * import from here instead of declaring their own API_URL.
 */

export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Typed fetch wrapper with automatic error handling.
 *
 * @param url - Full URL to fetch
 * @param init - Optional RequestInit (method, headers, body, etc.)
 * @returns Parsed JSON response typed as T
 * @throws Error with descriptive message on non-ok responses
 */
export async function apiFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);

  if (!response.ok) {
    const message = `API error ${response.status}: ${response.statusText}`;
    throw new Error(message);
  }

  return response.json();
}
