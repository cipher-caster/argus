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
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const indicatorSeriesRef = useRef<Map<string, ISeriesApi<"Line">[]>>(new Map());

  const theme = useThemeStore((s) => s.theme);
  const currentTheme = themes[theme];

  // Initialize chart
  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
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
          width: 1,
          style: 2,
          labelBackgroundColor: currentTheme.backgroundSecondary,
        },
        horzLine: {
          color: currentTheme.chart.crosshair,
          width: 1,
          style: 2,
          labelBackgroundColor: currentTheme.backgroundSecondary,
        },
      },
      rightPriceScale: {
        borderColor: currentTheme.border,
        scaleMargins: {
          top: 0.1,
          bottom: 0.2,
        },
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
    });

    const candlestickSeries = chart.addCandlestickSeries({
      upColor: currentTheme.positive,
      downColor: currentTheme.negative,
      borderUpColor: currentTheme.positive,
      borderDownColor: currentTheme.negative,
      wickUpColor: currentTheme.positive,
      wickDownColor: currentTheme.negative,
    });

    chartRef.current = chart;
    seriesRef.current = candlestickSeries;

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight,
        });
      }
    };

    window.addEventListener("resize", handleResize);
    handleResize();

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, [theme, currentTheme]);

  // Update chart data when candles change
  useEffect(() => {
    if (!seriesRef.current || !candles.length) return;

    const chartData: CandlestickData<Time>[] = candles.map((candle) => ({
      time: (candle.timestamp / 1000) as Time,
      open: candle.open,
      high: candle.high,
      low: candle.low,
      close: candle.close,
    }));

    seriesRef.current.setData(chartData);

    // Fit content to view
    if (chartRef.current) {
      chartRef.current.timeScale().fitContent();
    }
  }, [candles]);

  // Update indicator overlays
  useEffect(() => {
    if (!chartRef.current) return;

    const chart = chartRef.current;

    // Remove old indicator series
    indicatorSeriesRef.current.forEach((seriesList) => {
      seriesList.forEach((series) => {
        try {
          chart.removeSeries(series);
        } catch (e) {
          // Series may already be removed
        }
      });
    });
    indicatorSeriesRef.current.clear();

    // Add new indicator series for overlays only
    indicatorResults.forEach((result, resultIndex) => {
      if (result.type !== "overlay") return;

      // Find matching config for color
      const config = indicatorConfigs.find((c) => c.type === result.name && JSON.stringify(c.params) === JSON.stringify(result.params));
      const color = config?.color || "#6366f1";

      const seriesList: ISeriesApi<"Line">[] = [];

      // Handle different indicator types
      if (result.name === "bbands") {
        // Bollinger Bands: 3 lines
        const upperSeries = chart.addLineSeries({
          color: color,
          lineWidth: 1,
          lineStyle: 2,
          priceLineVisible: false,
        });
        const middleSeries = chart.addLineSeries({
          color: color,
          lineWidth: 1,
          priceLineVisible: false,
        });
        const lowerSeries = chart.addLineSeries({
          color: color,
          lineWidth: 1,
          lineStyle: 2,
          priceLineVisible: false,
        });

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
        // Single line indicators (EMA, SMA, LinReg)
        const lineSeries = chart.addLineSeries({
          color: color,
          lineWidth: 2,
          priceLineVisible: false,
        });

        const lineData: LineData<Time>[] = result.data
          .filter((d) => d.value !== undefined)
          .map((d) => ({
            time: (d.timestamp / 1000) as Time,
            value: d.value!,
          }));

        lineSeries.setData(lineData);
        seriesList.push(lineSeries);
      }

      indicatorSeriesRef.current.set(`${result.name}-${resultIndex}`, seriesList);
    });
  }, [indicatorResults, indicatorConfigs]);

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
      <div ref={chartContainerRef} className="chart-container" />

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

        .chart-header {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 16px 20px;
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
          padding: 4px 10px;
          font-size: 11px;
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
          flex: 1;
          min-height: 400px;
        }
      `}</style>
    </div>
  );
}

export const CandlestickChart = memo(CandlestickChartComponent);
