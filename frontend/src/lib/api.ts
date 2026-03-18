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

/**
 * Switch the active data provider
 */
export async function setProvider(provider: string): Promise<{ provider: string }> {
  const response = await fetch(`${API_URL}/api/provider`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ provider }),
  });

  if (!response.ok) {
    throw new Error(`Failed to switch provider: ${response.statusText}`);
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
  last_updated: number;
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
  last_updated: number;
}

export interface OracleSignalSummaryResponse {
  bullish_pct: number;
  bearish_pct: number;
  top_signals: string[];
  market_state: string;
  last_updated: number;
}

export interface TitanRadarItem {
  symbol: string;
  price: number;
  signal: string;
  confidence: number;
  trend: string;
  momentum: string;
  volatility: string;
  entry: number;
  tp: number;
  sl: number;
  advice: string;
  reasons: string[];
  mss_type?: "bullish" | "bearish" | null;
  sweep_type?: "bullish" | "bearish" | null;
}

export interface TitanRadarResponse {
  data: TitanRadarItem[];
  last_updated: number;
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
 * Fetch Mean Reversion (Contrarian Radar) data
 */
export async function fetchMeanReversion(timeframe: string = "1h", limit: number = 50): Promise<MeanReversionResponse> {
  const response = await fetch(`${API_URL}/api/analytics/contrarian-radar?timeframe=${timeframe}&limit=${limit}`);
  if (!response.ok) throw new Error("Failed to fetch contrarian radar");
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

export interface BestSetupItem {
  symbol: string;
  direction: "LONG" | "SHORT";
  conviction: number;
  entry: number;
  tp: number;
  sl: number;
  reason: string;
  oracle_score: number;
  titan_signal: string;
  /** Win rate % from Oracle backtest. null when total_trades < 10 (insufficient sample). Break-even is 33.3% at 2:1 RR. */
  win_rate: number | null;
  /** Number of simulated trades. null when < 10. */
  total_trades: number | null;
  /**
   * Swing+Macro MTF confluence. Titan signal confirmed on each timeframe.
   * Swing lane: 4h (entry trigger) + 1d (swing structure)
   * Macro lane: 12h (higher-TF bias) + 1w (macro/weekly direction)
   * null when data unavailable.
   */
  timeframe_confirmation: { "4h": boolean; "1d": boolean; "12h": boolean; "1w": boolean } | null;
}

export interface BestSetupsResponse {
  data: BestSetupItem[];
  last_updated: number;
}

/**
 * Fetch Best Setups (Oracle + Titan combined, high-conviction only)
 */
export async function fetchBestSetups(timeframe: string = "4h", limit: number = 50): Promise<BestSetupsResponse> {
  const response = await fetch(`${API_URL}/api/analytics/best-setups?timeframe=${timeframe}&limit=${limit}`);
  if (!response.ok) throw new Error("Failed to fetch best setups");
  return response.json();
}

/**
 * Fetch Titan Radar
 */
export async function fetchTitanRadar(limit: number = 50, timeframe: string = "4h"): Promise<TitanRadarResponse> {
  const response = await fetch(`${API_URL}/api/analytics/titan-radar?limit=${limit}&timeframe=${timeframe}`);
  if (!response.ok) throw new Error("Failed to fetch titan radar");
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
  active_fvg_type?: "bullish" | "bearish" | null;
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
  last_updated?: number;
}

export interface TitanStrategyResponse {
  symbol: string;
  timeframe: string;
  price: number;
  last_updated?: number;
  signal: string;
  confidence: number;
  trend: "BULLISH" | "BEARISH" | "NEUTRAL";
  mss_type?: "bullish" | "bearish" | null;
  mss_price?: number | null;
  sweep_type?: "bullish" | "bearish" | null;
  momentum: {
    status: string;
    rsi_val: number;
    is_overbought: boolean;
    is_oversold: boolean;
    macd_crossed: string;
  };
  volatility: {
    atr: number;
    squeeze: boolean;
  };
  targets: {
    entry: number;
    sl: number;
    tp: number;
    r_r: number;
  };
  sizing: string;
  indicators: {
    rsi: number;
    macd: number;
    adx: number | null;
    supertrend: number;
    ema20: number;
    ema50: number;
  };
}

/**
 * Fetch Titan Strategy analysis for a single symbol
 */
export async function fetchTitanStrategy(symbol: string, timeframe: string = "4h"): Promise<TitanStrategyResponse> {
  const response = await fetch(`${API_URL}/api/strategy/titan/${encodeURIComponent(symbol)}?timeframe=${timeframe}`);
  if (!response.ok) throw new Error(`Failed to fetch titan strategy: ${response.statusText}`);
  return response.json();
}

/**
 * Fetch Oracle Strategy analysis
 */
export interface SignalLogItem {
  id: number;
  symbol: string;
  direction: "LONG" | "SHORT";
  timeframe: string;
  entry: number;
  tp: number;
  sl: number;
  conviction: number;
  oracle_signal: string;
  titan_signal: string;
  oracle_score: number;
  titan_confidence: number;
  market_state: string;
  fired_reason: string;
  fired_at: number;
  source: "live" | "backtest";
  outcome: "OPEN" | "WIN" | "LOSS" | "REVIEW";
  resolved_at: number | null;
  resolved_price: number | null;
}

export interface SignalLogSummary {
  total: number;
  open: number;
  win: number;
  loss: number;
  review: number;
  win_rate: number | null;
}

export interface SignalLogResponse {
  data: SignalLogItem[];
  summary: SignalLogSummary;
  last_updated: number;
}

export interface SignalLogConfig {
  watchlist: string[];
  min_titan_confidence: number;
  review_days: number;
  block_sleeping: boolean;
  block_volatile: boolean;
  macro_guard: boolean;
  block_btc_sell: boolean;
}

export async function fetchSignalLogConfig(): Promise<SignalLogConfig> {
  const response = await fetch(`${API_URL}/api/analytics/signal-log/config`);
  if (!response.ok) throw new Error("Failed to fetch signal log config");
  return response.json();
}

export async function updateSignalLogConfig(config: SignalLogConfig): Promise<SignalLogConfig> {
  const response = await fetch(`${API_URL}/api/analytics/signal-log/config`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
  if (!response.ok) throw new Error("Failed to update signal log config");
  return response.json();
}

export async function fetchSignalLog(symbol?: string, source?: string, limit: number = 100): Promise<SignalLogResponse> {
  const params = new URLSearchParams({ limit: limit.toString() });
  if (symbol) params.append("symbol", symbol);
  if (source) params.append("source", source);
  const response = await fetch(`${API_URL}/api/analytics/signal-log?${params}`);
  if (!response.ok) throw new Error(`Failed to fetch signal log: ${response.statusText}`);
  return response.json();
}

export interface CoinBacktestStats {
  symbol: string;
  base: string;
  total: number;
  wins: number;
  losses: number;
  reviews: number;
  win_rate: number | null;
  profit_r: number;
  longs: number;
  shorts: number;
  long_wr: number | null;
  short_wr: number | null;
  avg_conviction: number;
}

export interface BacktestStatsResponse {
  coins: CoinBacktestStats[];
  overall: {
    total_signals: number;
    total_coins: number;
    win_rate: number | null;
    profit_r: number;
  } | null;
}

export async function fetchBacktestStats(): Promise<BacktestStatsResponse> {
  const response = await fetch(`${API_URL}/api/analytics/signal-log/stats?source=backtest`);
  if (!response.ok) throw new Error("Failed to fetch backtest stats");
  return response.json();
}

export async function fetchOracleStrategy(symbol: string, micro_tf: string = "1h", macro_tf: string = "1d"): Promise<OracleStrategyResponse> {
  const params = new URLSearchParams({
    micro_tf,
    macro_tf,
  });

  const response = await fetch(`${API_URL}/api/strategy/oracle/${encodeURIComponent(symbol)}?${params}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch oracle strategy: ${response.statusText}`);
  }

  return response.json();
}
