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
export async function fetchOHLCV(symbol: string, timeframe: string = "1h", limit: number = 100, end_timestamp?: number): Promise<OHLCVResponse> {
  const params = new URLSearchParams({
    timeframe,
    limit: limit.toString(),
  });
  if (end_timestamp) {
    params.append("end_timestamp", end_timestamp.toString());
  }

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

// --- Liquidation Heatmap Types ---

export interface TimeBucket {
  timestamp: number;
  price_buckets: Record<string, number>; // price_level -> volume
}

export interface OHLCVPoint {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
}

export interface LiquidationHeatmapResponse {
  symbol: string;
  time_buckets: TimeBucket[];
  price_min: number;
  price_max: number;
  max_intensity: number;
  ohlcv: OHLCVPoint[];
  bucket_size_seconds: number;
}

export interface LiquidationSymbolsResponse {
  symbols: string[];
  default: string;
}

/**
 * Fetch liquidation heatmap data
 */
export async function fetchLiquidationHeatmap(symbol: string = "BTCUSDT", lookbackHours: number = 24): Promise<LiquidationHeatmapResponse> {
  const params = new URLSearchParams({
    symbol,
    lookback_hours: lookbackHours.toString(),
  });

  const response = await fetch(`${API_URL}/api/liquidation/heatmap?${params}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch liquidation heatmap: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch supported liquidation symbols
 */
export async function fetchLiquidationSymbols(): Promise<LiquidationSymbolsResponse> {
  const response = await fetch(`${API_URL}/api/liquidation/symbols`);

  if (!response.ok) {
    throw new Error(`Failed to fetch liquidation symbols: ${response.statusText}`);
  }

  return response.json();
}

// --- Analytics Types ---

export interface FundingRatePoint {
  symbol: string;
  timestamp: number;
  funding_rate: number;
}

export interface FundingRateResponse {
  symbol: string;
  data: FundingRatePoint[];
}

export interface OpenInterestPoint {
  symbol: string;
  timestamp: number;
  open_interest: number;
  open_interest_value: number;
}

export interface OpenInterestResponse {
  symbol: string;
  data: OpenInterestPoint[];
}

export interface LongShortRatioPoint {
  symbol: string;
  timestamp: number;
  long_account: number;
  short_account: number;
  long_short_ratio: number;
}

export interface LongShortRatioResponse {
  symbol: string;
  data: LongShortRatioPoint[];
}

export interface AnalyticsSymbolsResponse {
  symbols: string[];
  default: string;
}

/**
 * Fetch funding rate history
 */
export async function fetchFundingRate(symbol: string = "BTCUSDT", limit: number = 100): Promise<FundingRateResponse> {
  const params = new URLSearchParams({
    symbol,
    limit: limit.toString(),
  });

  const response = await fetch(`${API_URL}/api/analytics/funding-rate?${params}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch funding rate: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch open interest history
 */
export async function fetchOpenInterest(symbol: string = "BTCUSDT", period: string = "1h", limit: number = 100): Promise<OpenInterestResponse> {
  const params = new URLSearchParams({
    symbol,
    period,
    limit: limit.toString(),
  });

  const response = await fetch(`${API_URL}/api/analytics/open-interest?${params}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch open interest: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch long/short ratio history
 */
export async function fetchLongShortRatio(symbol: string = "BTCUSDT", period: string = "1h", limit: number = 100): Promise<LongShortRatioResponse> {
  const params = new URLSearchParams({
    symbol,
    period,
    limit: limit.toString(),
  });

  const response = await fetch(`${API_URL}/api/analytics/long-short-ratio?${params}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch long/short ratio: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch supported analytics symbols
 */
export async function fetchAnalyticsSymbols(): Promise<AnalyticsSymbolsResponse> {
  const response = await fetch(`${API_URL}/api/analytics/symbols`);

  if (!response.ok) {
    throw new Error(`Failed to fetch analytics symbols: ${response.statusText}`);
  }

  return response.json();
}
