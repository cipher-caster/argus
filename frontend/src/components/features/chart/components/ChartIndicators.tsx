"use client";

import { IndicatorResult } from "@/lib/indicatorApi";
import { IndicatorConfig } from "@/stores/indicatorStore";
import { ISeriesApi, LineData, Time } from "lightweight-charts";
import { useEffect, useRef } from "react";
import { useChart } from "../context/ChartContext";

interface ChartIndicatorsProps {
  indicatorResults: IndicatorResult[];
  indicatorConfigs: IndicatorConfig[];
}

export function ChartIndicators({ indicatorResults, indicatorConfigs }: ChartIndicatorsProps) {
  const { chart } = useChart();
  const overlaySeriesRef = useRef<Map<string, ISeriesApi<"Line">[]>>(new Map());

  useEffect(() => {
    if (!chart) return;

    // Cleanup old series
    overlaySeriesRef.current.forEach((seriesList) => {
      seriesList.forEach((series) => {
        try {
          chart.removeSeries(series);
        } catch (e) {}
      });
    });
    overlaySeriesRef.current.clear();

    indicatorResults.forEach((result, resultIndex) => {
      if (result.type !== "overlay") return;

      const config = indicatorConfigs.find((c) => c.type === result.name && JSON.stringify(c.params) === JSON.stringify(result.params));
      if (config && !config.visible) return;

      const color = config?.color || "#6366f1";
      const seriesList: ISeriesApi<"Line">[] = [];

      if (result.name === "bbands") {
        const upperSeries = chart.addLineSeries({ color, lineWidth: 1, lineStyle: 2, priceLineVisible: false });
        const middleSeries = chart.addLineSeries({ color, lineWidth: 1, priceLineVisible: false });
        const lowerSeries = chart.addLineSeries({ color, lineWidth: 1, lineStyle: 2, priceLineVisible: false });

        const upperData: LineData<Time>[] = [];
        const middleData: LineData<Time>[] = [];
        const lowerData: LineData<Time>[] = [];

        result.data.forEach((d) => {
          const time = (d.timestamp / 1000) as Time;
          if (d.upper !== undefined) upperData.push({ time, value: d.upper });
          if (d.middle !== undefined) middleData.push({ time, value: d.middle });
          if (d.lower !== undefined) lowerData.push({ time, value: d.lower });
        });

        upperSeries.setData(upperData);
        middleSeries.setData(middleData);
        lowerSeries.setData(lowerData);
        seriesList.push(upperSeries, middleSeries, lowerSeries);
      } else {
        const lineSeries = chart.addLineSeries({ color, lineWidth: 2, priceLineVisible: false });
        const lineData: LineData<Time>[] = result.data
          .filter((d) => d.value !== undefined && d.value !== null && !isNaN(d.value))
          .map((d) => ({
            time: (d.timestamp / 1000) as Time,
            value: d.value!,
          }));
        lineSeries.setData(lineData);
        seriesList.push(lineSeries);
      }
      overlaySeriesRef.current.set(`${result.name}-${resultIndex}`, seriesList);
    });

    // Capture ref for cleanup to avoid stale-ref warning
    const overlay = overlaySeriesRef.current;
    return () => {
      overlay.forEach((seriesList) => {
        seriesList.forEach((series) => {
          try {
            chart.removeSeries(series);
          } catch (e) {}
        });
      });
      overlay.clear();
    };
  }, [chart, indicatorResults, indicatorConfigs]);

  return null;
}
