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
