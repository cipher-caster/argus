"use client";

import { IChartApi, ISeriesApi } from "lightweight-charts";
import { createContext, useContext, useState } from "react";

export interface ChartContextValue {
  chart: IChartApi | null;
  mainSeries: ISeriesApi<"Candlestick"> | null;
  setChart: (chart: IChartApi | null) => void;
  setMainSeries: (series: ISeriesApi<"Candlestick"> | null) => void;
  width: number;
  height: number;
  setDimensions: (width: number, height: number) => void;
}

export const ChartContext = createContext<ChartContextValue | null>(null);

export function ChartProvider({ children }: { children: React.ReactNode }) {
  const [chart, setChart] = useState<IChartApi | null>(null);
  const [mainSeries, setMainSeries] = useState<ISeriesApi<"Candlestick"> | null>(null);
  const [width, setWidth] = useState(0);
  const [height, setHeight] = useState(0);

  return (
    <ChartContext.Provider
      value={{
        chart,
        mainSeries,
        setChart,
        setMainSeries,
        width,
        height,
        setDimensions: (w, h) => {
          setWidth(w);
          setHeight(h);
        },
      }}
    >
      {children}
    </ChartContext.Provider>
  );
}

export function useChart() {
  const context = useContext(ChartContext);
  if (!context) {
    throw new Error("useChart must be used within a ChartProvider");
  }
  return context;
}
