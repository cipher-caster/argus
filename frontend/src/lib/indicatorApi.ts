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
