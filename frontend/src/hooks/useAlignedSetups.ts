"use client";

import { useBestSetups } from "@/hooks/useAnalyticsData";
import { BestSetupItem } from "@/lib/api";
import { useMemo } from "react";

interface AlignedSetupsResult {
  aligned: BestSetupItem[];
  counter: BestSetupItem[];
  isLoading: boolean;
}

/**
 * Hook that fetches best setups and splits them into regime-aligned and counter-trend.
 */
export function useAlignedSetups(regime: string | undefined, limit = 20): AlignedSetupsResult {
  const { data, isLoading } = useBestSetups("4h", limit);
  const setups = data?.data ?? [];

  const { aligned, counter } = useMemo(() => {
    if (!regime) return { aligned: [], counter: [] };
    const isBull = regime === "BULL";
    const isBear = regime === "BEAR";

    const aligned: BestSetupItem[] = [];
    const counter: BestSetupItem[] = [];

    for (const s of setups) {
      const isLong = s.direction === "LONG";
      if ((isBull && isLong) || (isBear && !isLong)) {
        aligned.push(s);
      } else {
        counter.push(s);
      }
    }

    return { aligned: aligned.slice(0, 3), counter: counter.slice(0, 2) };
  }, [setups, regime]);

  return { aligned, counter, isLoading };
}
