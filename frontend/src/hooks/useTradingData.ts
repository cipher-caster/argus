"use client";

import {
  fetchPositions,
  fetchTradeHistory,
  fetchTradingPortfolio,
  fetchTradingConfig,
  fetchTradingStats,
  closePosition,
  closeAllPositions,
  pauseTrading,
  updateTradingConfig,
  Position,
  PositionsResponse,
  HistoryResponse,
  TradingPortfolio,
  TradingConfig,
  TradingStats,
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
    onMutate: async (patch) => {
      await qc.cancelQueries({ queryKey: ["trading", "config"] });
      const previous = qc.getQueryData<TradingConfig>(["trading", "config"]);
      if (previous) {
        qc.setQueryData<TradingConfig>(["trading", "config"], { ...previous, ...patch });
      }
      return { previous };
    },
    onError: (error: Error, _patch, context) => {
      if (context?.previous) {
        qc.setQueryData(["trading", "config"], context.previous);
      }
      if (process.env.NODE_ENV === "development") console.error("Failed to update trading config:", error.message);
    },
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ["trading", "config"] });
      qc.invalidateQueries({ queryKey: ["trading", "portfolio"] });
    },
  });
}

export function useClosePosition() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => closePosition(id),
    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey: ["trading"] });
      const previous = qc.getQueryData<PositionsResponse>(["trading", "positions"]);
      if (previous) {
        qc.setQueryData<PositionsResponse>(["trading", "positions"], {
          ...previous,
          data: previous.data.map((p) => p.id === id ? { ...p, status: "CLOSED" as const } : p),
        });
      }
      return { previous };
    },
    onError: (error: Error, _id, context) => {
      if (context?.previous) {
        qc.setQueryData(["trading", "positions"], context.previous);
      }
      if (process.env.NODE_ENV === "development") console.error("Failed to close position:", error.message);
    },
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ["trading"] });
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
