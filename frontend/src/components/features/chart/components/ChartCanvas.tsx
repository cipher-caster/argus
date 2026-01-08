"use client";

import { useChartSettingsStore } from "@/stores/chartSettingsStore";
import { themes, useThemeStore } from "@/stores/themeStore";
import { ColorType, createChart } from "lightweight-charts";
import { ReactNode, useEffect, useRef } from "react";
import { useChart } from "../context/ChartContext";

interface ChartCanvasProps {
  children?: ReactNode;
  className?: string; // For layout styling
}

export function ChartCanvas({ children, className }: ChartCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const { chart: contextChart, setChart, mainSeries: contextMainSeries, setMainSeries, setDimensions, width, height } = useChart();

  const theme = useThemeStore((s) => s.theme);
  const currentTheme = themes[theme];
  const chartColors = useChartSettingsStore((s) => s.colors);

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
    width,
    height,
  });

  // Resize Observer
  useEffect(() => {
    if (!containerRef.current) return;

    const resizeObserver = new ResizeObserver((entries) => {
      if (!entries.length) return;
      const { width, height } = entries[0].contentRect;
      setDimensions(width, height);
      if (contextChart) {
        contextChart.applyOptions({ width, height });
      }
    });

    resizeObserver.observe(containerRef.current);

    return () => resizeObserver.disconnect();
  }, [contextChart, setDimensions]);

  // Initial Resize
  useEffect(() => {
    const timer = setTimeout(() => {
      if (containerRef.current) {
        setDimensions(containerRef.current.clientWidth, containerRef.current.clientHeight);
      }
    }, 50);
    return () => clearTimeout(timer);
  }, [setDimensions]);

  // Initialize Chart
  useEffect(() => {
    if (!containerRef.current) return;

    // We check if dimensions are > 0 to avoid the 0x0 issue
    if (width === 0 || height === 0) return;

    const seriesOptions = {
      upColor: chartColors.upColor || currentTheme.positive,
      downColor: chartColors.downColor || currentTheme.negative,
      borderUpColor: chartColors.borderUpColor || currentTheme.positive,
      borderDownColor: chartColors.borderDownColor || currentTheme.negative,
      wickUpColor: chartColors.wickUpColor || currentTheme.positive,
      wickDownColor: chartColors.wickDownColor || currentTheme.negative,
    };

    if (!contextChart) {
      try {
        const newChart = createChart(containerRef.current, getChartOptions(width, height));
        setChart(newChart);

        const series = newChart.addCandlestickSeries(seriesOptions);
        setMainSeries(series);
      } catch (e) {
        console.error("Failed to create chart", e);
      }
    } else {
      contextChart.applyOptions(getChartOptions(width, height));
      contextMainSeries?.applyOptions(seriesOptions);
    }

    // Cleanup: We don't want to destroy the chart here unless the component unmounts.
    // But since context outlives this component (via provider being higher),
    // actually, if ChartCanvas is unmounted (e.g. conditional render), we probably DO want to destroy the chart?
    // In our case, ChartCanvas is always rendered if data is there.
    // If we navigate away, Provider unmounts, state is lost (good).

    return () => {
      // If we unmount Canvas, we should cleanup chart instance from the canvas DOM
      // The provider state needs to be reset?
      // Let's assume on Unmount we cleanup.
      // Actually, if we just cleanup contextChart.remove(), the reference in Provider becomes stale?
      // We should setChart(null).
    };
  }, [width, height, theme, currentTheme, chartColors]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (contextChart) {
        contextChart.remove();
        setChart(null);
        setMainSeries(null);
      }
    };
  }, []); // Run on mount/unmount only

  return (
    <div className={className} style={{ position: "relative" }}>
      <div ref={containerRef} className="absolute inset-0" />
      {children}
    </div>
  );
}
