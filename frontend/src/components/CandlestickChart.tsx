"use client";

/**
 * Interactive Candlestick Chart Component with Indicator Overlays
 * Powered by TradingView's lightweight-charts
 */

import { Candle } from "@/lib/api";
import { IndicatorResult } from "@/lib/indicatorApi";
import { IndicatorConfig } from "@/stores/indicatorStore";
import { themes, useThemeStore } from "@/stores/themeStore";
import { CandlestickData, ColorType, createChart, IChartApi, ISeriesApi, LineData, Time } from "lightweight-charts";
import { memo, useEffect, useRef } from "react";

interface CandlestickChartProps {
  candles: Candle[];
  symbol: string;
  isLoading?: boolean;
  indicatorResults?: IndicatorResult[];
  indicatorConfigs?: IndicatorConfig[];
}

function CandlestickChartComponent({ candles, symbol, isLoading, indicatorResults = [], indicatorConfigs = [] }: CandlestickChartProps) {
  const mainContainerRef = useRef<HTMLDivElement>(null);
  const paneRefs = useRef<Map<string, HTMLDivElement>>(new Map());

  const mainChartRef = useRef<IChartApi | null>(null);
  const paneChartRefs = useRef<Map<string, IChartApi>>(new Map());

  const mainSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const overlaySeriesRef = useRef<Map<string, ISeriesApi<"Line">[]>>(new Map());
  const paneSeriesRef = useRef<Map<string, ISeriesApi<"Line" | "Histogram">[]>>(new Map());

  const theme = useThemeStore((s) => s.theme);
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

  // Initialize charts (Main + Panes)
  useEffect(() => {
    if (!mainContainerRef.current) return;

    // --- Main Chart ---
    if (!mainChartRef.current) {
      const width = mainContainerRef.current.clientWidth;
      const height = mainContainerRef.current.clientHeight;
      const chart = createChart(mainContainerRef.current, getChartOptions(width, height));

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
    } else {
      // Update Options if theme changes
      const width = mainContainerRef.current.clientWidth;
      const height = mainContainerRef.current.clientHeight;
      mainChartRef.current.applyOptions(getChartOptions(width, height));
      mainSeriesRef.current?.applyOptions({
        upColor: currentTheme.positive,
        downColor: currentTheme.negative,
        borderUpColor: currentTheme.positive,
        borderDownColor: currentTheme.negative,
        wickUpColor: currentTheme.positive,
        wickDownColor: currentTheme.negative,
      });
    }

    // --- Pane Charts ---
    // Only create charts for "pane" type indicators that are visible
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
        // Pane height is fixed by CSS (150px), but we should read it
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

      // Main Chart Resize
      if (mainContainerRef.current && mainChartRef.current) {
        const width = mainContainerRef.current.clientWidth;
        const height = mainContainerRef.current.clientHeight;
        mainChartRef.current.applyOptions({ width, height });
      }

      // Pane Charts Resize
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

  // Update Main Chart Data
  useEffect(() => {
    if (!mainSeriesRef.current || !candles.length) return;

    const chartData: CandlestickData<Time>[] = candles.map((candle) => ({
      time: (candle.timestamp / 1000) as Time,
      open: candle.open,
      high: candle.high,
      low: candle.low,
      close: candle.close,
    }));

    mainSeriesRef.current.setData(chartData);

    if (mainChartRef.current) {
      mainChartRef.current.timeScale().fitContent();
    }
  }, [candles]);

  // Update Indicator Data (Both Overlay and Panes)
  useEffect(() => {
    if (!mainChartRef.current) return;
    const mainChart = mainChartRef.current;

    // --- 1. Handle Overlays ---
    // Remove old overlay series
    overlaySeriesRef.current.forEach((seriesList) => {
      seriesList.forEach((series) => {
        try {
          mainChart.removeSeries(series);
        } catch (e) {}
      });
    });
    overlaySeriesRef.current.clear();

    // Populate Overlays
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
        // Standard Line
        const lineSeries = mainChart.addLineSeries({ color, lineWidth: 2, priceLineVisible: false });
        const lineData: LineData<Time>[] = result.data
          .filter((d) => d.value !== undefined)
          .map((d) => ({
            time: (d.timestamp / 1000) as Time,
            value: d.value!,
          }));
        lineSeries.setData(lineData);
        seriesList.push(lineSeries);
      }
      overlaySeriesRef.current.set(`${result.name}-${resultIndex}`, seriesList);
    });

    // --- 2. Handle Panes ---
    const paneIndicators = indicatorConfigs.filter((i) => i.visible && i.indicatorType === "pane");

    paneIndicators.forEach((config) => {
      const chart = paneChartRefs.current.get(config.id);
      if (!chart) return;

      // Find result for this config
      const result = indicatorResults.find((r) => r.name === config.type && JSON.stringify(r.params) === JSON.stringify(config.params));
      if (!result) return;

      // Clear existing series for this pane
      const existingSeries = paneSeriesRef.current.get(config.id) || [];
      existingSeries.forEach((s) => {
        try {
          chart.removeSeries(s);
        } catch (e) {}
      });

      const newSeriesList: ISeriesApi<"Line" | "Histogram">[] = [];
      const color = config.color;

      if (result.name === "macd") {
        // MACD Line
        const macdSeries = chart.addLineSeries({ color: currentTheme.info || "#3b82f6", lineWidth: 1, title: "" });
        // Signal Line
        const signalSeries = chart.addLineSeries({ color: currentTheme.warning || "#f59e0b", lineWidth: 1, title: "" });
        // Histogram
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
        const rsiData = result.data.map((d) => ({ time: (d.timestamp / 1000) as Time, value: d.value! }));
        rsiSeries.setData(rsiData);

        // Add levels (30/70)
        rsiSeries.createPriceLine({ price: 70, color: currentTheme.chart.text, lineWidth: 1, lineStyle: 2, axisLabelVisible: false, title: "" });
        rsiSeries.createPriceLine({ price: 30, color: currentTheme.chart.text, lineWidth: 1, lineStyle: 2, axisLabelVisible: false, title: "" });

        newSeriesList.push(rsiSeries);
      } else {
        // Generic Line Pane (OBV etc)
        const lineSeries = chart.addLineSeries({ color, lineWidth: 1, title: config.displayName });
        const data = result.data.map((d) => ({ time: (d.timestamp / 1000) as Time, value: d.value! }));
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
      <div className="chart-header">
        <span className="chart-symbol">{symbol}</span>
        {isLoading && <span className="chart-loading">Loading...</span>}
        {indicatorConfigs.filter((i) => i.visible && i.indicatorType === "overlay").length > 0 && (
          <div className="indicator-badges">
            {indicatorConfigs
              .filter((i) => i.visible && i.indicatorType === "overlay")
              .map((i) => (
                <span key={i.id} className="indicator-badge" style={{ borderColor: i.color, color: i.color }}>
                  {i.displayName}
                </span>
              ))}
          </div>
        )}
      </div>

      {/* Main Chart */}
      <div ref={mainContainerRef} className="chart-container main-chart" />

      {/* Pane Indicators */}
      {visiblePaneConfigs.map((config) => (
        <div key={config.id} className="pane-wrapper">
          <div className="pane-header">
            <span className="pane-title" style={{ color: config.color }}>
              {config.displayName}
            </span>
          </div>
          <div
            ref={(el) => {
              if (el) paneRefs.current.set(config.id, el);
              else paneRefs.current.delete(config.id);
            }}
            className="chart-container pane-chart"
          />
        </div>
      ))}

      <style jsx>{`
        .chart-wrapper {
          width: 100%;
          min-height: 100%;
          display: flex;
          flex-direction: column;
          background: var(--chart-bg);
          border-radius: 12px;
          overflow: hidden;
          border: 1px solid var(--border-color);
        }

        .chart-header {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px 20px;
          background: var(--bg-secondary);
          border-bottom: 1px solid var(--border-color);
        }

        .chart-symbol {
          font-size: 18px;
          font-weight: 600;
          color: var(--text-primary);
          letter-spacing: 0.5px;
        }

        .chart-loading {
          font-size: 12px;
          color: var(--accent-primary);
          animation: pulse 1.5s ease-in-out infinite;
        }

        .indicator-badges {
          display: flex;
          gap: 8px;
          margin-left: auto;
        }

        .indicator-badge {
          padding: 2px 8px;
          font-size: 10px;
          font-weight: 500;
          border: 1px solid;
          border-radius: 4px;
          background: var(--bg-tertiary);
        }

        @keyframes pulse {
          0%,
          100% {
            opacity: 0.5;
          }
          50% {
            opacity: 1;
          }
        }

        .chart-container {
          width: 100%;
        }

        .main-chart {
          flex: 1;
          min-height: 0;
        }

        .pane-wrapper {
          border-top: 1px solid var(--border-color);
          background: var(--bg-secondary);
          display: flex;
          flex-direction: column;
        }

        .pane-header {
          padding: 4px 10px;
          font-size: 11px;
          font-weight: 600;
          background: var(--bg-tertiary);
        }

        .pane-chart {
          height: 150px;
        }
      `}</style>
    </div>
  );
}

export const CandlestickChart = memo(CandlestickChartComponent);
