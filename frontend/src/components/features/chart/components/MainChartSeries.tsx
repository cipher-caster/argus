"use client";

import { Candle } from "@/lib/api";
import { Time } from "lightweight-charts";
import { useEffect, useRef } from "react";
import { useChart } from "../context/ChartContext";

interface MainChartSeriesProps {
  candles: Candle[];
  onLoadMore?: () => void;
  isLoadingMore?: boolean;
  timeframe: string;
}

export function MainChartSeries({ candles, onLoadMore, isLoadingMore, timeframe }: MainChartSeriesProps) {
  const { chart, mainSeries } = useChart();
  const prevTimeframeRef = useRef(timeframe);

  // Infinite Scroll Handler
  useEffect(() => {
    if (!chart) return;

    const handleVisibleRangeChange = (range: any) => {
      if (!range) return;
      if (range.from < 10 && !isLoadingMore && onLoadMore) {
        onLoadMore();
      }
    };

    chart.timeScale().subscribeVisibleLogicalRangeChange(handleVisibleRangeChange);

    return () => {
      chart.timeScale().unsubscribeVisibleLogicalRangeChange(handleVisibleRangeChange);
    };
  }, [chart, isLoadingMore, onLoadMore]);

  // Data Sync
  useEffect(() => {
    if (!mainSeries || !chart) return;
    if (!candles.length) {
      mainSeries.setData([]);
      return;
    }

    const isTimeframeChange = prevTimeframeRef.current !== timeframe;
    prevTimeframeRef.current = timeframe;

    let savedRange: { from: number; to: number } | null = null;
    if (!isTimeframeChange) {
      const currentRange = chart.timeScale().getVisibleLogicalRange();
      if (currentRange) {
        savedRange = { from: currentRange.from, to: currentRange.to };
      }
    }

    const chartData = candles.map((candle) => ({
      time: (candle.timestamp / 1000) as Time,
      open: candle.open,
      high: candle.high,
      low: candle.low,
      close: candle.close,
    }));

    mainSeries.setData(chartData);

    if (savedRange) {
      chart.timeScale().setVisibleLogicalRange(savedRange);
    } else {
      // Only scroll to end on initial load or timeframe change
      if (isTimeframeChange || candles.length > 0) {
        // Should check if it's "initial" load?
        // If we had no data before, it's effectively initial.
        chart.timeScale().scrollToPosition(0, true);
      }
    }
  }, [candles, timeframe, mainSeries, chart]);

  return null; // Logic only
}
