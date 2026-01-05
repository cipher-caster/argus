/**
 * API functions for market overview
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface CoinInfo {
  rank: number;
  symbol: string;
  name: string;
  price: number;
  change_24h: number | null;
  volume_24h: number | null;
  high_24h: number | null;
  low_24h: number | null;
}

export interface CoinsResponse {
  coins: CoinInfo[];
  total: number;
  page: number;
  page_size: number;
}

export interface MarketSummary {
  total_coins: number;
  provider: string;
}

/**
 * Fetch market summary stats
 */
export async function fetchMarketSummary(): Promise<MarketSummary> {
  const response = await fetch(`${API_URL}/api/market/summary`);

  if (!response.ok) {
    throw new Error(`Failed to fetch market summary: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch paginated coins list
 */
export async function fetchCoins(params: { page?: number; pageSize?: number; search?: string; sortBy?: string; sortOrder?: string }): Promise<CoinsResponse> {
  const searchParams = new URLSearchParams();

  if (params.page) searchParams.set("page", params.page.toString());
  if (params.pageSize) searchParams.set("page_size", params.pageSize.toString());
  if (params.search) searchParams.set("search", params.search);
  if (params.sortBy) searchParams.set("sort_by", params.sortBy);
  if (params.sortOrder) searchParams.set("sort_order", params.sortOrder);

  const response = await fetch(`${API_URL}/api/market/coins?${searchParams}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch coins: ${response.statusText}`);
  }

  return response.json();
}
