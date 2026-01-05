/**
 * API client for fetching market data
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Candle {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface OHLCVResponse {
  symbol: string;
  timeframe: string;
  provider: string;
  candles: Candle[];
}

export interface SymbolInfo {
  symbol: string;
  base: string;
  quote: string;
}

export interface TickerResponse {
  symbol: string;
  price: number | null;
  provider: string;
}

/**
 * Fetch OHLCV candlestick data
 */
export async function fetchOHLCV(symbol: string, timeframe: string = "1h", limit: number = 100): Promise<OHLCVResponse> {
  const params = new URLSearchParams({
    timeframe,
    limit: limit.toString(),
  });

  const response = await fetch(`${API_URL}/api/ohlcv/${encodeURIComponent(symbol)}?${params}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch OHLCV: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch available trading symbols
 */
export async function fetchSymbols(): Promise<SymbolInfo[]> {
  const response = await fetch(`${API_URL}/api/symbols`);

  if (!response.ok) {
    throw new Error(`Failed to fetch symbols: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch current ticker price
 */
export async function fetchTicker(symbol: string): Promise<TickerResponse> {
  const response = await fetch(`${API_URL}/api/ticker/${encodeURIComponent(symbol)}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch ticker: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch current provider info
 */
export async function fetchProviderInfo(): Promise<{ provider: string }> {
  const response = await fetch(`${API_URL}/api/provider`);

  if (!response.ok) {
    throw new Error(`Failed to fetch provider: ${response.statusText}`);
  }

  return response.json();
}
