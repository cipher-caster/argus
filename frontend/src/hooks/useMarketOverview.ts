"use client";

/**
 * React Query hooks for market overview data
 */

import { fetchCoins, fetchMarketSummary } from "@/lib/marketApi";
import { useQuery } from "@tanstack/react-query";

/**
 * Hook for fetching market summary
 */
export function useMarketSummary() {
  return useQuery({
    queryKey: ["market-summary"],
    queryFn: fetchMarketSummary,
    refetchInterval: 60000, // Refresh every minute
  });
}

/**
 * Hook for fetching coins list with pagination
 */
export function useCoins(params: { page?: number; pageSize?: number; search?: string; sortBy?: string; sortOrder?: string }) {
  return useQuery({
    queryKey: ["coins", params],
    queryFn: () => fetchCoins(params),
    refetchInterval: 30000, // Refresh every 30s
  });
}
