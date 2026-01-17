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

// --- Analytics Types ---

export interface AnalyticsSymbolsResponse {
  symbols: string[];
  default: string;
}

export interface ScreenerItem {
  symbol: string;
  price: number;
  score: number;
  confidence: string;
  bias: string;
  state: string;
  liquidity: string;
  strength_vs_btc: string;
  opportunity: string;
  advice: string;
}

export interface ScreenerResponse {
  data: ScreenerItem[];
}

export interface MarketHealthResponse {
  summary: {
    total_coins: number;
    bullish_pct: number;
    bearish_pct: number;
    squeezing_pct: number;
  };
  volatility: {
    DANGER: number;
    ACTIVE: number;
    STABLE: number;
  };
}

export interface LiquiditySweepItem {
  symbol: string;
  bull_sweep: boolean;
  bear_sweep: boolean;
  swept_level: number;
  type: string;
}

export interface LiquiditySweepResponse {
  data: LiquiditySweepItem[];
}

export interface RelativeStrengthItem {
  symbol: string;
  performance_relative_pct: number;
  strength: string;
  current_ratio: number;
}

export interface RelativeStrengthResponse {
  data: RelativeStrengthItem[];
}

export interface MeanReversionItem {
  symbol: string;
  is_extended: boolean;
  extension_atr: number;
  opportunity: string;
  price: number;
  mean: number;
  target: number;
}

export interface MeanReversionResponse {
  data: MeanReversionItem[];
}

export interface OracleSignalSummaryResponse {
  bullish_pct: number;
  bearish_pct: number;
  top_signals: string[];
  market_state: string;
}

/**
 * Fetch supported analytics symbols
 */
export async function fetchAnalyticsSymbols(limit: number = 20): Promise<AnalyticsSymbolsResponse> {
  const response = await fetch(`${API_URL}/api/analytics/symbols?limit=${limit}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch analytics symbols: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch Oracle Screener results
 */
export async function fetchOracleScreener(timeframe: string = "1h", limit: number = 50): Promise<ScreenerResponse> {
  const response = await fetch(`${API_URL}/api/analytics/screener?timeframe=${timeframe}&limit=${limit}`);
  if (!response.ok) throw new Error("Failed to fetch screener");
  return response.json();
}

/**
 * Fetch Market Health metrics
 */
export async function fetchMarketHealth(timeframe: string = "1h", limit: number = 100): Promise<MarketHealthResponse> {
  const response = await fetch(`${API_URL}/api/analytics/market-health?timeframe=${timeframe}&limit=${limit}`);
  if (!response.ok) throw new Error("Failed to fetch market health");
  return response.json();
}

/**
 * Fetch Liquidity Sweeps
 */
export async function fetchLiquiditySweeps(timeframe: string = "1h", limit: number = 50): Promise<LiquiditySweepResponse> {
  const response = await fetch(`${API_URL}/api/analytics/liquidity-sweeps?timeframe=${timeframe}&limit=${limit}`);
  if (!response.ok) throw new Error("Failed to fetch sweeps");
  return response.json();
}

/**
 * Fetch Relative Strength data
 */
export async function fetchRelativeStrength(timeframe: string = "1h", limit: number = 50): Promise<RelativeStrengthResponse> {
  const response = await fetch(`${API_URL}/api/analytics/relative-strength?timeframe=${timeframe}&limit=${limit}`);
  if (!response.ok) throw new Error("Failed to fetch relative strength");
  return response.json();
}

/**
 * Fetch Mean Reversion (Contrarian Radar) data
 */
export async function fetchMeanReversion(timeframe: string = "1h", limit: number = 50): Promise<MeanReversionResponse> {
  const response = await fetch(`${API_URL}/api/analytics/contrarian-radar?timeframe=${timeframe}&limit=${limit}`);
  if (!response.ok) throw new Error("Failed to fetch radar");
  return response.json();
}

/**
 * Fetch Oracle Signal Summary for Dashboard
 */
export async function fetchOracleSignalSummary(): Promise<OracleSignalSummaryResponse> {
  const response = await fetch(`${API_URL}/api/analytics/signal-summary`);
  if (!response.ok) throw new Error("Failed to fetch signal summary");
  return response.json();
}

// --- Strategy Types ---

export interface OracleStrategyResponse {
  symbol: string;
  micro_tf: string;
  macro_tf: string;
  price: number;
  signal: "STRONG_BUY" | "BUY" | "STRONG_SELL" | "SELL" | "NEUTRAL";
  confidence: string;
  bias: "BULLISH" | "BEARISH" | "NEUTRAL";
  state: string;
  volatility: string;
  earnest: {
    score: number;
    voters: Record<string, number>;
  };
  macro: {
    score: number;
    bias: string;
    details: Record<string, boolean>;
  };
  targets: {
    tp1: number;
    tp2: number;
    sl: number;
  };
  advice: string;
  historical_signals: Array<{
    timestamp: number;
    signal: string;
    price: number;
  }>;
  performance: {
    total_trades: number;
    win_rate: number;
    net_profit: number;
  };
}

/**
 * Fetch Oracle Strategy analysis
 */
export async function fetchOracleStrategy(symbol: string, micro_tf: string = "1h", macro_tf: string = "1d", strategy_mode: string = "prophet"): Promise<OracleStrategyResponse> {
  const params = new URLSearchParams({
    micro_tf,
    macro_tf,
    strategy_mode,
  });

  const response = await fetch(`${API_URL}/api/strategy/oracle/${encodeURIComponent(symbol)}?${params}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch oracle strategy: ${response.statusText}`);
  }

  return response.json();
}
