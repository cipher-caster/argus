"use client";

/**
 * Interactive Candlestick Chart Component with Indicator Overlays
 * Powered by TradingView's lightweight-charts
 */

import { Candle } from "@/lib/api";
import { IndicatorResult } from "@/lib/indicatorApi";
import { useChartSettingsStore } from "@/stores/chartSettingsStore";
import { IndicatorConfig } from "@/stores/indicatorStore";
import { themes, useThemeStore } from "@/stores/themeStore";
import { CandlestickData, ColorType, createChart, IChartApi, ISeriesApi, LineData, Time } from "lightweight-charts";
import { memo, useEffect, useRef, useState } from "react";
import { ChartHeader } from "./chart/ChartHeader";
import { IndicatorPane } from "./chart/IndicatorPane";
import { IndicatorModal } from "./IndicatorModal";

interface CandlestickChartProps {
  candles: Candle[];
  symbol: string;
  isLoading?: boolean;
  indicatorResults?: IndicatorResult[];
  indicatorConfigs?: IndicatorConfig[];
  onLoadMore?: () => void;
  isLoadingMore?: boolean;
  timeframe?: string;
  onTimeframeChange?: (tf: string) => void;
}

function CandlestickChartComponent({ candles, symbol, isLoading, indicatorResults = [], indicatorConfigs = [], onLoadMore, isLoadingMore, timeframe, onTimeframeChange }: CandlestickChartProps) {
  const mainContainerRef = useRef<HTMLDivElement>(null);
  const paneRefs = useRef<Map<string, HTMLDivElement>>(new Map());

  const mainChartRef = useRef<IChartApi | null>(null);
  const paneChartRefs = useRef<Map<string, IChartApi>>(new Map());

  const mainSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const overlaySeriesRef = useRef<Map<string, ISeriesApi<"Line">[]>>(new Map());
  const paneSeriesRef = useRef<Map<string, ISeriesApi<"Line" | "Histogram">[]>>(new Map());

  const theme = useThemeStore((s) => s.theme);
  const { colors: chartColors } = useChartSettingsStore();

  const [isIndicatorModalOpen, setIsIndicatorModalOpen] = useState(false);
  const [editingIndicator, setEditingIndicator] = useState<IndicatorConfig | null>(null);

  // Track if we are already loading to avoid double calls
  const isLoadingMoreRef = useRef(false);
  useEffect(() => {
    isLoadingMoreRef.current = !!isLoadingMore;
  }, [isLoadingMore]);

  // Keep ref to latest onLoadMore to avoid stale closure issues
  const onLoadMoreRef = useRef(onLoadMore);
  useEffect(() => {
    onLoadMoreRef.current = onLoadMore;
  }, [onLoadMore]);

  const currentTheme = themes[theme];

  // Helper to create chart options
  const getChartOptions = (width: number, height: number) => ({
    layout: {
      background: { type: ColorType.Solid, color: currentTheme.chart.background },
      textColor: currentTheme.chart.text,
    },
    grid: {
      vertLines: { color: currentTheme.chart.gridLines },
      horzLines: { color: currentTheme.chart.gridLines },
    },
    crosshair: {
      mode: 1,
      vertLine: {
        color: currentTheme.chart.crosshair,
        width: 1 as 1,
        style: 2,
        labelBackgroundColor: currentTheme.backgroundSecondary,
      },
      horzLine: {
        color: currentTheme.chart.crosshair,
        width: 1 as 1,
        style: 2,
        labelBackgroundColor: currentTheme.backgroundSecondary,
      },
    },
    rightPriceScale: {
      borderColor: currentTheme.border,
      scaleMargins: {
        top: 0.1,
        bottom: 0.1,
      },
      visible: true,
    },
    timeScale: {
      borderColor: currentTheme.border,
      timeVisible: true,
      secondsVisible: false,
    },
    handleScale: {
      axisPressedMouseMove: true,
    },
    handleScroll: {
      vertTouchDrag: true,
    },
    width,
    height,
  });

  // --- Effect 1: Initialize Chart (Mount/Unmount) ---
  useEffect(() => {
    if (!mainContainerRef.current) return;

    const width = mainContainerRef.current.clientWidth;
    const height = mainContainerRef.current.clientHeight;
    const chart = createChart(mainContainerRef.current, getChartOptions(width, height));

    // Infinite Scroll Handler
    chart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
      if (!range) return;
      if (!onLoadMoreRef.current) return;
      if (range.from < 10 && !isLoadingMoreRef.current) {
        onLoadMoreRef.current();
      }
    });

    const candlestickSeries = chart.addCandlestickSeries({
      upColor: currentTheme.positive,
      downColor: currentTheme.negative,
      borderUpColor: currentTheme.positive,
      borderDownColor: currentTheme.negative,
      wickUpColor: currentTheme.positive,
      wickDownColor: currentTheme.negative,
    });

    mainChartRef.current = chart;
    mainSeriesRef.current = candlestickSeries;

    return () => {
      chart.remove();
      mainChartRef.current = null;
      mainSeriesRef.current = null;
    };
  }, []);

  // --- Effect 2: Update Options (Theme/Settings/Resize) ---
  useEffect(() => {
    if (!mainChartRef.current || !mainContainerRef.current) return;

    const width = mainContainerRef.current.clientWidth;
    const height = mainContainerRef.current.clientHeight;

    mainChartRef.current.applyOptions(getChartOptions(width, height));

    mainSeriesRef.current?.applyOptions({
      upColor: chartColors.upColor || currentTheme.positive,
      downColor: chartColors.downColor || currentTheme.negative,
      borderUpColor: chartColors.borderUpColor || currentTheme.positive,
      borderDownColor: chartColors.borderDownColor || currentTheme.negative,
      wickUpColor: chartColors.wickUpColor || currentTheme.positive,
      wickDownColor: chartColors.wickDownColor || currentTheme.negative,
    });
  }, [theme, currentTheme, chartColors]);

  // --- Effect 3: Manage Pane Charts & Resize ---
  useEffect(() => {
    const paneIndicators = indicatorConfigs.filter((i) => i.visible && i.indicatorType === "pane");

    // Cleanup removed panes
    const currentPaneIds = new Set(paneIndicators.map((i) => i.id));
    paneChartRefs.current.forEach((chart, id) => {
      if (!currentPaneIds.has(id)) {
        chart.remove();
        paneChartRefs.current.delete(id);
        paneSeriesRef.current.delete(id);
      }
    });

    // Create/Update panes
    paneIndicators.forEach((ind) => {
      const container = paneRefs.current.get(ind.id);
      if (!container) return;

      let chart = paneChartRefs.current.get(ind.id);
      if (!chart) {
        const width = container.clientWidth;
        const height = container.clientHeight || 150;
        chart = createChart(container, getChartOptions(width, height));
        paneChartRefs.current.set(ind.id, chart);

        // Sync with main chart
        if (mainChartRef.current) {
          const main = mainChartRef.current;
          chart.timeScale().subscribeVisibleTimeRangeChange((range) => {
            if (range) main.timeScale().setVisibleRange(range);
          });
          main.timeScale().subscribeVisibleTimeRangeChange((range) => {
            if (range) chart?.timeScale().setVisibleRange(range);
          });
        }
      } else {
        const width = container.clientWidth;
        const height = container.clientHeight || 150;
        chart.applyOptions(getChartOptions(width, height));
      }
    });

    // Resize Observer
    const resizeObserver = new ResizeObserver((entries) => {
      if (!entries || entries.length === 0) return;

      if (mainContainerRef.current && mainChartRef.current) {
        const width = mainContainerRef.current.clientWidth;
        const height = mainContainerRef.current.clientHeight;
        mainChartRef.current.applyOptions({ width, height });
      }

      paneIndicators.forEach((ind) => {
        const container = paneRefs.current.get(ind.id);
        const chart = paneChartRefs.current.get(ind.id);
        if (container && chart) {
          const width = container.clientWidth;
          const height = container.clientHeight;
          chart.applyOptions({ width, height });
        }
      });
    });

    if (mainContainerRef.current) resizeObserver.observe(mainContainerRef.current);
    paneRefs.current.forEach((el) => resizeObserver.observe(el));

    return () => {
      resizeObserver.disconnect();
    };
  }, [theme, currentTheme, indicatorConfigs]);

  // --- Effect 4: Update Main Chart Data ---
  useEffect(() => {
    if (!mainSeriesRef.current || !candles.length) return;

    let savedRange: { from: number; to: number } | null = null;
    if (mainChartRef.current) {
      const currentRange = mainChartRef.current.timeScale().getVisibleLogicalRange();
      if (currentRange) {
        savedRange = { from: currentRange.from, to: currentRange.to };
      }
    }

    const chartData: CandlestickData<Time>[] = candles.map((candle) => ({
      time: (candle.timestamp / 1000) as Time,
      open: candle.open,
      high: candle.high,
      low: candle.low,
      close: candle.close,
    }));

    mainSeriesRef.current.setData(chartData);

    if (mainChartRef.current) {
      if (savedRange) {
        mainChartRef.current.timeScale().setVisibleLogicalRange(savedRange);
      } else {
        mainChartRef.current.timeScale().scrollToPosition(0, true);
      }
    }
  }, [candles]);

  // --- Effect 5: Update Indicator Data (Both Overlay and Panes) ---
  useEffect(() => {
    if (!mainChartRef.current) return;
    const mainChart = mainChartRef.current;

    // Handle Overlays
    overlaySeriesRef.current.forEach((seriesList) => {
      seriesList.forEach((series) => {
        try {
          mainChart.removeSeries(series);
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
        const upperSeries = mainChart.addLineSeries({ color, lineWidth: 1, lineStyle: 2, priceLineVisible: false });
        const middleSeries = mainChart.addLineSeries({ color, lineWidth: 1, priceLineVisible: false });
        const lowerSeries = mainChart.addLineSeries({ color, lineWidth: 1, lineStyle: 2, priceLineVisible: false });

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
        const lineSeries = mainChart.addLineSeries({ color, lineWidth: 2, priceLineVisible: false });
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

    // Handle Panes
    const paneIndicators = indicatorConfigs.filter((i) => i.visible && i.indicatorType === "pane");

    paneIndicators.forEach((config) => {
      const chart = paneChartRefs.current.get(config.id);
      if (!chart) return;

      const result = indicatorResults.find((r) => r.name === config.type && JSON.stringify(r.params) === JSON.stringify(config.params));
      if (!result) return;

      const existingSeries = paneSeriesRef.current.get(config.id) || [];
      existingSeries.forEach((s) => {
        try {
          chart.removeSeries(s);
        } catch (e) {}
      });

      const newSeriesList: ISeriesApi<"Line" | "Histogram">[] = [];
      const color = config.color;

      if (result.name === "macd") {
        const macdSeries = chart.addLineSeries({ color: currentTheme.info || "#3b82f6", lineWidth: 1, title: "" });
        const signalSeries = chart.addLineSeries({ color: currentTheme.warning || "#f59e0b", lineWidth: 1, title: "" });
        const histSeries = chart.addHistogramSeries({ title: "" });

        const macdData: LineData<Time>[] = [];
        const signalData: LineData<Time>[] = [];
        const histData: any[] = [];

        result.data.forEach((d) => {
          const time = (d.timestamp / 1000) as Time;
          if (d.macd !== undefined) macdData.push({ time, value: d.macd });
          if (d.signal !== undefined) signalData.push({ time, value: d.signal });
          if (d.histogram !== undefined) {
            histData.push({
              time,
              value: d.histogram,
              color: d.histogram >= 0 ? currentTheme.positive : currentTheme.negative,
            });
          }
        });

        macdSeries.setData(macdData);
        signalSeries.setData(signalData);
        histSeries.setData(histData);
        newSeriesList.push(macdSeries, signalSeries, histSeries);
      } else if (result.name === "rsi") {
        const rsiSeries = chart.addLineSeries({ color, lineWidth: 1, title: "" });
        const rsiData = result.data.filter((d) => d.value !== undefined && d.value !== null && !isNaN(d.value)).map((d) => ({ time: (d.timestamp / 1000) as Time, value: d.value! }));
        rsiSeries.setData(rsiData);

        rsiSeries.createPriceLine({
          price: 70,
          color: currentTheme.chart.text,
          lineWidth: 1,
          lineStyle: 2,
          axisLabelVisible: false,
          title: "",
        });
        rsiSeries.createPriceLine({
          price: 30,
          color: currentTheme.chart.text,
          lineWidth: 1,
          lineStyle: 2,
          axisLabelVisible: false,
          title: "",
        });

        newSeriesList.push(rsiSeries);
      } else {
        const lineSeries = chart.addLineSeries({ color, lineWidth: 1, title: config.displayName });
        const data = result.data.filter((d) => d.value !== undefined && d.value !== null && !isNaN(d.value)).map((d) => ({ time: (d.timestamp / 1000) as Time, value: d.value! }));
        lineSeries.setData(data);
        newSeriesList.push(lineSeries);
      }

      paneSeriesRef.current.set(config.id, newSeriesList);
      chart.timeScale().fitContent();
    });
  }, [indicatorResults, indicatorConfigs, candles]);

  const visiblePaneConfigs = indicatorConfigs.filter((i) => i.visible && i.indicatorType === "pane");

  return (
    <div className="chart-wrapper">
      <ChartHeader
        symbol={symbol}
        isLoading={isLoading}
        timeframe={timeframe}
        onTimeframeChange={onTimeframeChange}
        indicatorConfigs={indicatorConfigs}
        onAddIndicator={() => {
          setEditingIndicator(null);
          setIsIndicatorModalOpen(true);
        }}
        onEditIndicator={(ind) => {
          setEditingIndicator(ind);
          setIsIndicatorModalOpen(true);
        }}
      />

      {/* Main Chart */}
      <div ref={mainContainerRef} className="chart-container main-chart" />

      {/* Pane Indicators */}
      {visiblePaneConfigs.map((config) => (
        <IndicatorPane
          key={config.id}
          config={config}
          onContainerRef={(el) => {
            if (el) paneRefs.current.set(config.id, el);
            else paneRefs.current.delete(config.id);
          }}
        />
      ))}

      <IndicatorModal isOpen={isIndicatorModalOpen} onClose={() => setIsIndicatorModalOpen(false)} editingIndicator={editingIndicator} />

      <style jsx>{`
        .chart-wrapper {
          width: 100%;
          height: 100%;
          display: flex;
          flex-direction: column;
          background: var(--chart-bg);
          border-radius: 12px;
          overflow: hidden;
          border: 1px solid var(--border-color);
        }

        .chart-container {
          width: 100%;
        }

        .main-chart {
          flex: 1;
          min-height: 200px;
        }
      `}</style>
    </div>
  );
}

export const CandlestickChart = memo(CandlestickChartComponent);
