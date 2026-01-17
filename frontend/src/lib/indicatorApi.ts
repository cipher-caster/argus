/**
 * API functions for indicators
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface IndicatorParam {
  name: string;
  type: string;
  default: number;
  min: number;
  max: number;
}

export interface IndicatorDefinition {
  name: string;
  display_name: string;
  type: "overlay" | "pane";
  params: IndicatorParam[];
  description: string;
}

export interface IndicatorData {
  timestamp: number;
  value?: number;
  // For Bollinger Bands
  lower?: number;
  middle?: number;
  upper?: number;
  // For MACD
  macd?: number;
  signal?: number;
  histogram?: number;
}

export interface IndicatorResult {
  name: string;
  type: string;
  params: Record<string, number>;
  data: IndicatorData[];
}

export interface CalculateResponse {
  symbol: string;
  timeframe: string;
  results: IndicatorResult[];
}

/**
 * Fetch list of available indicators
 */
export async function fetchIndicators(): Promise<IndicatorDefinition[]> {
  const response = await fetch(`${API_URL}/api/indicators/`);

  if (!response.ok) {
    throw new Error(`Failed to fetch indicators: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Calculate indicators for a symbol
 */
export async function calculateIndicators(symbol: string, timeframe: string, indicators: Array<{ type: string; params: Record<string, number> }>, limit: number = 300): Promise<CalculateResponse> {
  const response = await fetch(`${API_URL}/api/indicators/calculate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      symbol,
      timeframe,
      limit,
      indicators,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to calculate indicators: ${response.statusText}`);
  }

  return response.json();
}

// Dashboard Market Indicators

export interface IndicatorValue {
  value: number;
  label: string;
  timestamp?: string;
  min_value?: number;
  max_value?: number;
  history: number[];
}

export interface MarketCapStats {
  value: number;
  metric_type?: string;
  change_1d: number;
  regime: "BULLISH" | "NEUTRAL" | "BEARISH";
  regime_detail?: string;
  min_value: number;
  max_value: number;
  history: number[];
}

export interface DashboardIndicators {
  btc_volatility: IndicatorValue | null;
  market_adx: IndicatorValue | null;
  total_market_cap: MarketCapStats | null;
  btc_dominance: IndicatorValue | null;
  updated_at: string;
}

/**
 * Fetch dashboard market indicators
 */
export async function fetchDashboardIndicators(): Promise<DashboardIndicators> {
  const response = await fetch(`${API_URL}/api/indicators/market/dashboard`);

  if (!response.ok) {
    throw new Error(`Failed to fetch dashboard indicators: ${response.statusText}`);
  }

  return response.json();
}
