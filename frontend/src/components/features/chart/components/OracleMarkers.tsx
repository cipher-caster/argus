"use client";

import { useStrategyOracle } from "@/hooks/useStrategyOracle";
import { useEffect } from "react";
import { useChart } from "../context/ChartContext";
import { Time, SeriesMarker } from "lightweight-charts";

interface OracleMarkersProps {
  symbol: string;
  timeframe: string;
}

export function OracleMarkers({ symbol, timeframe }: OracleMarkersProps) {
  const { chart, mainSeries } = useChart();
  const { data } = useStrategyOracle(symbol, timeframe);

  useEffect(() => {
    if (!mainSeries || !data?.historical_signals) return;

    const markers: SeriesMarker<Time>[] = data.historical_signals.map((sig) => {
      const isBuy = sig.signal.includes("BUY");
      return {
        time: (sig.timestamp / 1000) as Time,
        position: isBuy ? "belowBar" : "aboveBar",
        color: isBuy ? "#10b981" : "#f43f5e",
        shape: isBuy ? "arrowUp" : "arrowDown",
        text: sig.signal.replace("_", " "),
        size: 1,
      };
    });

    // Sort markers by time as required by lightweight-charts
    markers.sort((a, b) => (a.time as number) - (b.time as number));

    mainSeries.setMarkers(markers);

    return () => {
      if (mainSeries) mainSeries.setMarkers([]);
    };
  }, [mainSeries, data?.historical_signals]);

  return null;
}
