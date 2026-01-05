"use client";

/**
 * Interactive Candlestick Chart Component with Indicator Overlays
 * Powered by TradingView's lightweight-charts
 */

import { Candle } from "@/lib/api";
import { IndicatorResult } from "@/lib/indicatorApi";
import { useChartSettingsStore } from "@/stores/chartSettingsStore";
import { IndicatorConfig, useIndicatorStore } from "@/stores/indicatorStore";
import { themes, useThemeStore } from "@/stores/themeStore";
import { CandlestickData, ColorType, createChart, IChartApi, ISeriesApi, LineData, Time } from "lightweight-charts";
import { BarChart2, CandlestickChart as CandleIcon, ChevronDown, Edit2, Eye, EyeOff, PlusCircle, Search, Trash2, X } from "lucide-react";
import { memo, useEffect, useRef, useState } from "react";
import { IndicatorModal } from "./IndicatorModal";
import { TimeframeSelector } from "./TimeframeSelector";
import { Dropdown } from "./ui/Dropdown";

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

  const toggleVisibility = useIndicatorStore((s) => s.toggleVisibility);
  const removeIndicator = useIndicatorStore((s) => s.removeIndicator);

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

    // Create Main Chart
    const width = mainContainerRef.current.clientWidth;
    const height = mainContainerRef.current.clientHeight;
    // Initial creation with current theme
    const chart = createChart(mainContainerRef.current, getChartOptions(width, height));

    // Infinite Scroll Handler
    chart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
      if (!range) return;
      if (!onLoadMoreRef.current) return;
      if (range.from < 10 && !isLoadingMoreRef.current) {
        onLoadMoreRef.current();
      }
    });

    // Create Main Series (Initial)
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

    // Cleanup function
    return () => {
      console.log("[CandlestickChart] Cleaning up chart");
      chart.remove();
      mainChartRef.current = null;
      mainSeriesRef.current = null;
    };
  }, []); // Run once on mount

  // --- Effect 2: Update Options (Theme/Settings/Resize) ---
  useEffect(() => {
    if (!mainChartRef.current || !mainContainerRef.current) return;

    console.log("[CandlestickChart] Updating options with colors:", chartColors);

    const width = mainContainerRef.current.clientWidth;
    const height = mainContainerRef.current.clientHeight;

    // Apply layout options
    mainChartRef.current.applyOptions(getChartOptions(width, height));

    // Apply series options
    mainSeriesRef.current?.applyOptions({
      upColor: chartColors.upColor || currentTheme.positive,
      downColor: chartColors.downColor || currentTheme.negative,
      borderUpColor: chartColors.borderUpColor || currentTheme.positive,
      borderDownColor: chartColors.borderDownColor || currentTheme.negative,
      wickUpColor: chartColors.wickUpColor || currentTheme.positive,
      wickDownColor: chartColors.wickDownColor || currentTheme.negative,
    });
  }, [theme, currentTheme, chartColors]); // Run when theme or settings change
  // --- Effect 3: Manage Pane Charts & Resize ---
  useEffect(() => {
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

    // Save current visible range before update (to preserve scroll position)
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
        // Restore the saved visible range to keep the view stable
        mainChartRef.current.timeScale().setVisibleLogicalRange(savedRange);
      } else {
        // First load - scroll to latest
        mainChartRef.current.timeScale().scrollToPosition(0, true);
      }
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
        const rsiData = result.data.filter((d) => d.value !== undefined && d.value !== null && !isNaN(d.value)).map((d) => ({ time: (d.timestamp / 1000) as Time, value: d.value! }));
        rsiSeries.setData(rsiData);

        // Add levels (30/70)
        rsiSeries.createPriceLine({ price: 70, color: currentTheme.chart.text, lineWidth: 1, lineStyle: 2, axisLabelVisible: false, title: "" });
        rsiSeries.createPriceLine({ price: 30, color: currentTheme.chart.text, lineWidth: 1, lineStyle: 2, axisLabelVisible: false, title: "" });

        newSeriesList.push(rsiSeries);
      } else {
        // Generic Line Pane (OBV etc)
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
      <div className="chart-header">
        {/* Symbol Section */}
        <div className="header-group symbol-group">
          <Search size={18} className="icon-search" />
          <span className="chart-symbol">{symbol}</span>
          <div className="provider-badge-small">
            <div className="diamond-icon"></div>
          </div>
        </div>

        <div className="header-separator"></div>

        {/* Comparison */}
        <button className="icon-btn-circle" title="Compare or Add Symbol">
          <PlusCircle size={18} />
        </button>

        <div className="header-separator"></div>

        {/* Timeframes */}
        <div className="header-group timeframe-group">{timeframe && onTimeframeChange && <TimeframeSelector selected={timeframe} onChange={onTimeframeChange} />}</div>

        <div className="header-separator"></div>

        {/* Chart Type */}
        <div className="header-group">
          <button className="icon-btn" title="Chart Style">
            <CandleIcon size={20} />
          </button>
        </div>

        <div className="header-separator"></div>

        {/* Indicators */}
        <div className="header-group">
          <div className="indicators-button-group">
            <button
              className="text-icon-btn main-btn"
              onClick={() => {
                setEditingIndicator(null);
                setIsIndicatorModalOpen(true);
              }}
            >
              <BarChart2 size={18} />
              <span>Indicators</span>
            </button>
            <Dropdown
              trigger={
                <button className="dropdown-arrow-btn">
                  <ChevronDown size={14} />
                </button>
              }
            >
              <div className="active-indicators-menu">
                <div className="menu-header">Active Indicators</div>
                {indicatorConfigs.length === 0 ? (
                  <div className="no-indicators">No indicators added</div>
                ) : (
                  indicatorConfigs.map((ind) => (
                    <div key={ind.id} className="indicator-menu-item">
                      <div className="indicator-info">
                        <div className="color-dot" style={{ background: ind.color }}></div>
                        <span className="display-name">{ind.displayName}</span>
                      </div>
                      <div className="indicator-menu-actions">
                        <button onClick={() => toggleVisibility(ind.id)}>{ind.visible ? <Eye size={14} /> : <EyeOff size={14} />}</button>
                        <button
                          onClick={() => {
                            setEditingIndicator(ind);
                            setIsIndicatorModalOpen(true);
                          }}
                        >
                          <Edit2 size={14} />
                        </button>
                        <button onClick={() => removeIndicator(ind.id)} className="delete">
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </Dropdown>
          </div>
          {indicatorConfigs.filter((i) => i.visible && i.indicatorType === "overlay").length > 0 && (
            <div className="indicator-badges">
              {indicatorConfigs
                .filter((i) => i.visible && i.indicatorType === "overlay")
                .map((i) => (
                  <span
                    key={i.id}
                    className="indicator-badge interactable"
                    style={{ borderColor: i.color, color: i.color }}
                    onClick={() => {
                      setEditingIndicator(i);
                      setIsIndicatorModalOpen(true);
                    }}
                  >
                    {i.displayName}
                    <button
                      className="indicator-remove-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        removeIndicator(i.id);
                      }}
                    >
                      <X size={10} />
                    </button>
                  </span>
                ))}
            </div>
          )}
        </div>

        {isLoading && <span className="chart-loading">Loading...</span>}
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

      <IndicatorModal isOpen={isIndicatorModalOpen} onClose={() => setIsIndicatorModalOpen(false)} editingIndicator={editingIndicator} />

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
          height: 38px;
          padding: 0 12px;
          background: var(--bg-secondary);
          border-bottom: 1px solid var(--border-color);
          gap: 4px;
        }

        .header-group {
          display: flex;
          align-items: center;
          gap: 4px;
        }

        .header-separator {
          width: 1px;
          height: 20px;
          background: var(--border-color);
          margin: 0 4px;
        }

        .chart-symbol {
          font-weight: 700;
          font-size: 14px;
          color: var(--text-primary);
          margin: 0 4px;
        }

        .icon-search {
          color: var(--text-muted);
          cursor: pointer;
        }

        .icon-search:hover {
          color: var(--text-primary);
        }

        .provider-badge-small {
          display: flex;
          align-items: center;
          gap: 2px;
          padding: 2px;
          border-radius: 4px;
          cursor: pointer;
        }

        .provider-badge-small:hover {
          background: var(--bg-tertiary);
        }

        .diamond-icon {
          width: 12px;
          height: 12px;
          border: 1px solid var(--text-muted);
          transform: rotate(45deg);
        }

        .icon-btn-circle {
          width: 24px;
          height: 24px;
          border-radius: 50%;
          border: 1px solid var(--border-color);
          background: transparent;
          color: var(--text-muted);
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all 0.1s;
        }

        .icon-btn-circle:hover {
          color: var(--text-primary);
          border-color: var(--text-muted);
          background: var(--bg-tertiary);
        }

        .icon-btn {
          width: 28px;
          height: 28px;
          border: none;
          background: transparent;
          color: var(--text-muted);
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          border-radius: 4px;
        }

        .icon-btn:hover {
          color: var(--text-primary);
          background: var(--bg-tertiary);
        }

        .indicators-button-group {
          display: flex;
          align-items: center;
          background: transparent;
          border-radius: 4px;
          overflow: hidden;
        }

        .indicators-button-group:hover {
          background: var(--bg-tertiary);
        }

        .text-icon-btn {
          height: 28px;
          padding: 0 6px;
          border: none;
          background: transparent;
          color: var(--text-muted);
          display: flex;
          align-items: center;
          gap: 4px;
          cursor: pointer;
          font-weight: 600;
          font-size: 13px;
        }

        .text-icon-btn:hover {
          color: var(--text-primary);
        }

        .dropdown-arrow-btn {
          height: 28px;
          padding: 0 2px;
          border: none;
          background: transparent;
          color: var(--text-muted);
          cursor: pointer;
          display: flex;
          align-items: center;
        }

        .dropdown-arrow-btn:hover {
          color: var(--text-primary);
          background: rgba(0, 0, 0, 0.05);
        }

        .active-indicators-menu {
          min-width: 220px;
          padding: 4px 0;
        }

        .active-indicators-menu .menu-header {
          padding: 8px 12px;
          font-size: 11px;
          font-weight: 700;
          color: var(--text-muted);
          text-transform: uppercase;
        }

        .indicator-menu-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 6px 12px;
        }

        .indicator-menu-item:hover {
          background: var(--bg-tertiary);
        }

        .indicator-info {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .color-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }

        .display-name {
          font-size: 13px;
          color: var(--text-primary);
        }

        .indicator-menu-actions {
          display: flex;
          gap: 4px;
        }

        .indicator-menu-actions button {
          background: transparent;
          border: none;
          padding: 4px;
          cursor: pointer;
          color: var(--text-muted);
          border-radius: 4px;
          display: flex;
          align-items: center;
        }

        .indicator-menu-actions button:hover {
          color: var(--text-primary);
          background: rgba(0, 0, 0, 0.05);
        }

        .indicator-menu-actions button.delete:hover {
          color: var(--negative);
        }

        .no-indicators {
          padding: 12px;
          font-size: 12px;
          color: var(--text-muted);
          text-align: center;
        }

        .icon-tiny {
          color: var(--text-muted);
        }

        .chart-loading {
          font-size: 11px;
          color: var(--accent-primary);
          margin-left: auto;
          animation: pulse 1.5s ease-in-out infinite;
        }

        .indicator-badges {
          display: flex;
          gap: 4px;
          margin-left: 8px;
        }

        .indicator-badge {
          padding: 1px 6px;
          font-size: 9px;
          font-weight: 600;
          border: 1px solid;
          border-radius: 2px;
          background: transparent;
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
          padding: 2px 10px;
          font-size: 10px;
          font-weight: 600;
          background: var(--bg-secondary);
        }

        .pane-chart {
          height: 120px;
        }

        .indicator-badge.interactable {
          cursor: pointer;
          display: inline-flex;
          align-items: center;
          gap: 4px;
          padding-right: 4px;
        }

        .indicator-badge.interactable:hover {
          background: var(--bg-tertiary);
        }

        .indicator-remove-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          background: transparent;
          border: none;
          color: currentColor;
          opacity: 0.6;
          cursor: pointer;
          padding: 0;
          width: 14px;
          height: 14px;
          border-radius: 50%;
        }

        .indicator-remove-btn:hover {
          opacity: 1;
          background: rgba(0, 0, 0, 0.1);
        }
      `}</style>
    </div>
  );
}

export const CandlestickChart = memo(CandlestickChartComponent);
