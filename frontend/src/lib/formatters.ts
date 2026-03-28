/**
 * Standardized formatting utilities for Argus
 */

/**
 * Format price with dynamic precision based on value magnitude.
 * - >= 1000: 2 decimals, comma separated
 * - >= 1: 2 decimals
 * - >= 0.0001: 5 decimals
 * - < 0.0001: 8 decimals
 */
export function formatPrice(price: number | null | undefined): string {
  if (price === null || price === undefined) return "—";

  if (price >= 1000) {
    return price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  } else if (price >= 1) {
    return price.toFixed(2);
  } else if (price >= 0.0001) {
    return price.toFixed(5);
  } else {
    return price.toFixed(8);
  }
}

/**
 * Format volume/market cap with K/M/B suffixes.
 * @param val Value in base units
 * @param currencyPrefix defaults to true (adds $)
 */
export function formatVolume(val: number | null | undefined, currencyPrefix: boolean = true): string {
  if (val === null || val === undefined) return "—";

  const prefix = currencyPrefix ? "$" : "";

  if (val >= 1e12) return `${prefix}${(val / 1e12).toFixed(2)}T`;
  if (val >= 1e9) return `${prefix}${(val / 1e9).toFixed(2)}B`;
  if (val >= 1e6) return `${prefix}${(val / 1e6).toFixed(2)}M`;
  if (val >= 1e3) return `${prefix}${(val / 1e3).toFixed(0)}K`; // Changed to match CoinTable logic (no decimals for K usually)

  return `${prefix}${val.toFixed(2)}`;
}

/**
 * Format percentage change with sign.
 * @param val Percentage value (e.g. 5.2 for 5.2%)
 * @param includeSign Explicitly include + sign for positive numbers (default: true)
 */
export function formatChange(val: number | null | undefined, includeSign: boolean = true): string {
  if (val === null || val === undefined) return "—";

  const sign = includeSign && val >= 0 ? "+" : "";
  return `${sign}${val.toFixed(2)}%`;
}

/**
 * Format a regular number with fixed precision
 */
export function formatNumber(val: number | null | undefined, decimals: number = 2): string {
  if (val === null || val === undefined) return "—";
  return val.toFixed(decimals);
}

/**
 * Format price for compact/table display.
 * - >= 1000: 2 decimals, comma separated
 * - >= 1: 4 decimals
 * - < 1: 6 decimals
 */
export function formatPriceCompact(price: number): string {
  if (price >= 1000) return price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  if (price >= 1) return price.toFixed(4);
  return price.toFixed(6);
}

/**
 * Format a unix-ms timestamp as "Mon DD, YYYY HH:MM"
 */
export function formatDateTime(ms: number): string {
  const d = new Date(ms);
  const mon = d.toLocaleString("en-US", { month: "short" });
  const day = d.getDate();
  const yr = d.getFullYear();
  const hh = d.getHours().toString().padStart(2, "0");
  const mm = d.getMinutes().toString().padStart(2, "0");
  return `${mon} ${day}, ${yr} ${hh}:${mm}`;
}

/**
 * Relative time string from a unix-ms timestamp.
 */
export function timeAgo(ms: number): string {
  const diff = Date.now() - ms;
  const h = Math.floor(diff / 3_600_000);
  const d = Math.floor(diff / 86_400_000);
  if (d >= 1) return `${d}d ago`;
  if (h >= 1) return `${h}h ago`;
  return "< 1h ago";
}

/**
 * Duration string between two unix-ms timestamps.
 */
export function duration(from: number | null, to: number | null): string {
  if (!from || !to) return "—";
  const ms = to - from;
  const h = Math.floor(ms / 3_600_000);
  const d = Math.floor(ms / 86_400_000);
  if (d >= 1) return `${d}d ${h % 24}h`;
  if (h >= 1) return `${h}h`;
  return "< 1h";
}

/**
 * Percentage change between two values with sign.
 */
export function formatPercentageChange(from: number, to: number, dir: "LONG" | "SHORT" = "LONG"): string {
  const raw = dir === "LONG" ? ((to - from) / from) * 100 : ((from - to) / from) * 100;
  return (raw >= 0 ? "+" : "") + raw.toFixed(1) + "%";
}
