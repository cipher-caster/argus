"use client";

import {
  fetchTradingPortfolio,
  fetchPositions,
  fetchTradeHistory,
  fetchTradingConfig,
  fetchTradingStats,
  updateTradingConfig,
  closePosition,
  closeAllPositions,
  pauseTrading,
  TradingConfig,
} from "@/lib/api";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

const STALE = 30_000; // 30s

export function useTradingPortfolio() {
  return useQuery({
    queryKey: ["trading", "portfolio"],
    queryFn: fetchTradingPortfolio,
    staleTime: STALE,
    refetchInterval: STALE,
  });
}

export function useActivePositions() {
  return useQuery({
    queryKey: ["trading", "positions", "active"],
    queryFn: () => fetchPositions("OPEN,PENDING"),
    staleTime: STALE,
    refetchInterval: STALE,
  });
}

export function usePositions(status?: string) {
  return useQuery({
    queryKey: ["trading", "positions", status],
    queryFn: () => fetchPositions(status),
    staleTime: STALE,
    refetchInterval: STALE,
  });
}

export function useTradeHistory(limit = 50, offset = 0) {
  return useQuery({
    queryKey: ["trading", "history", limit, offset],
    queryFn: () => fetchTradeHistory(limit, offset),
    staleTime: STALE,
    refetchInterval: 60_000,
  });
}

export function useTradingConfig() {
  return useQuery({
    queryKey: ["trading", "config"],
    queryFn: fetchTradingConfig,
    staleTime: 60_000,
  });
}

export function useTradingStats() {
  return useQuery({
    queryKey: ["trading", "stats"],
    queryFn: fetchTradingStats,
    staleTime: STALE,
    refetchInterval: 60_000,
  });
}

export function useUpdateTradingConfig() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (patch: Partial<TradingConfig>) => updateTradingConfig(patch),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["trading", "config"] });
      qc.invalidateQueries({ queryKey: ["trading", "portfolio"] });
    },
    onError: (error: Error) => {
      console.error("Failed to update trading config:", error.message);
    },
  });
}

export function useClosePosition() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => closePosition(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["trading"] });
    },
    onError: (error: Error) => {
      console.error("Failed to close position:", error.message);
    },
  });
}

export function useCloseAllPositions() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: closeAllPositions,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["trading"] });
    },
    onError: (error: Error) => {
      console.error("Failed to close all positions:", error.message);
    },
  });
}

export function usePauseTrading() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: pauseTrading,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["trading", "config"] });
      qc.invalidateQueries({ queryKey: ["trading", "portfolio"] });
    },
    onError: (error: Error) => {
      console.error("Failed to pause trading:", error.message);
    },
  });
}
