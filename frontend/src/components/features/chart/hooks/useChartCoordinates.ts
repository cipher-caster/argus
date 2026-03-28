"use client";

import { Point } from "@/stores/drawingStore";
import { Time } from "lightweight-charts";
import { useEffect, useState } from "react";
import { useChart } from "../context/ChartContext";

export interface ChartCoordinateAPI {
  pointToPixels: (point: Point) => { x: number; y: number } | null;
  pixelsToPoint: (x: number, y: number) => Point | null;
  renderTick: number;
  chartWidth: number;
  chartHeight: number;
}

export function useChartCoordinates(): ChartCoordinateAPI {
  const { chart, mainSeries, width, height } = useChart();
  const [renderTick, setRenderTick] = useState(0);

  useEffect(() => {
    if (!chart) return;
    const handler = () => setRenderTick((t) => t + 1);
    chart.timeScale().subscribeVisibleTimeRangeChange(handler);
    return () => chart.timeScale().unsubscribeVisibleTimeRangeChange(handler);
  }, [chart]);

  const pointToPixels = (point: Point): { x: number; y: number } | null => {
    if (!chart || !mainSeries) return null;
    const x = chart.timeScale().timeToCoordinate(point.time as unknown as Time);
    const y = mainSeries.priceToCoordinate(point.price);
    if (x === null || y === null) return null;
    return { x, y };
  };

  const pixelsToPoint = (x: number, y: number): Point | null => {
    if (!chart || !mainSeries) return null;
    const time = chart.timeScale().coordinateToTime(x);
    const price = mainSeries.coordinateToPrice(y);
    if (time === null || price === null) return null;
    return { time: time as unknown as number, price };
  };

  return { pointToPixels, pixelsToPoint, renderTick, chartWidth: width, chartHeight: height };
}
