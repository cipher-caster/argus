"use client";

import { useEffect, useState } from "react";

export interface CoinMeta {
  id: string;
  symbol: string;
  name: string;
  image: string;
}

export interface CoinMetaData {
  updated_at: string;
  count: number;
  coins: CoinMeta[];
}

// Cache for coin metadata lookup
let coinMetaCache: Map<string, CoinMeta> | null = null;

/**
 * Load coin metadata from local JSON file
 * Returns a Map keyed by symbol (uppercase) for fast lookup
 */
export async function loadCoinMeta(): Promise<Map<string, CoinMeta>> {
  if (coinMetaCache) {
    return coinMetaCache;
  }

  try {
    const res = await fetch("/data/coins/coins.json");
    if (!res.ok) {
      return new Map();
    }

    const data: CoinMetaData = await res.json();

    // Build lookup map by symbol
    const map = new Map<string, CoinMeta>();
    for (const coin of data.coins) {
      // Store by uppercase symbol for easy matching
      map.set(coin.symbol.toUpperCase(), coin);
      // Also store by {SYMBOL}/USDT format for Binance compatibility
      map.set(`${coin.symbol.toUpperCase()}/USDT`, coin);
    }

    coinMetaCache = map;
    return map;
  } catch {
    return new Map();
  }
}

/**
 * Hook to get coin metadata lookup
 */
export function useCoinMeta() {
  const [coinMeta, setCoinMeta] = useState<Map<string, CoinMeta>>(new Map());
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadCoinMeta()
      .then(setCoinMeta)
      .finally(() => setIsLoading(false));
  }, []);

  return { coinMeta, isLoading };
}

/**
 * Get coin image URL, with fallback to colored circle
 */
export function getCoinImageUrl(symbol: string, coinMeta: Map<string, CoinMeta>): string | null {
  const meta = coinMeta.get(symbol.toUpperCase()) || coinMeta.get(`${symbol.toUpperCase()}/USDT`);
  return meta?.image || null;
}

/**
 * Get coin name from metadata
 */
export function getCoinName(symbol: string, coinMeta: Map<string, CoinMeta>): string {
  const meta = coinMeta.get(symbol.toUpperCase()) || coinMeta.get(`${symbol.toUpperCase()}/USDT`);
  return meta?.name || symbol.split("/")[0];
}
