"use client";

import { IndicatorResult } from "@/lib/indicatorApi";
import { IndicatorConfig } from "@/stores/indicatorStore";
import { themes, useThemeStore } from "@/stores/themeStore";
import { ColorType, createChart, IChartApi, ISeriesApi, LineData, Time } from "lightweight-charts";
import { useEffect, useRef } from "react";
import { useChart } from "../context/ChartContext";
import { IndicatorPane } from "./IndicatorPane";

interface ChartPanesProps {
  indicatorConfigs: IndicatorConfig[];
  indicatorResults: IndicatorResult[];
}

export function ChartPanes({ indicatorConfigs, indicatorResults }: ChartPanesProps) {
  const { chart: mainChart } = useChart();
  const paneRefs = useRef<Map<string, HTMLDivElement>>(new Map());
  const paneChartRefs = useRef<Map<string, IChartApi>>(new Map());
  const paneSeriesRef = useRef<Map<string, ISeriesApi<"Line" | "Histogram">[]>>(new Map());

  const theme = useThemeStore((s) => s.theme);
  const currentTheme = themes[theme];

  const getChartOptions = (width: number, height: number) => ({
    layout: {
      background: { type: ColorType.Solid, color: currentTheme.chart.background },
      textColor: currentTheme.chart.text,
    },
    grid: {
      vertLines: { color: currentTheme.chart.gridLines },
      horzLines: { color: currentTheme.chart.gridLines },
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

  // Manage Panes (Create/Remove/Resize)
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
        if (mainChart) {
          const main = mainChart;
          chart.timeScale().subscribeVisibleTimeRangeChange((range) => {
            if (range && range.from && range.to) {
              main.timeScale().setVisibleRange(range);
            }
          });
          main.timeScale().subscribeVisibleTimeRangeChange((range) => {
            if (range && range.from && range.to) {
              chart?.timeScale().setVisibleRange(range);
            }
          });
        }
      } else {
        const width = container.clientWidth;
        const height = container.clientHeight || 150;
        chart.applyOptions(getChartOptions(width, height));
      }
    });

    // Resize logic is tricky with multiple panes.
    // We can use a single resize observer for all?
    const resizeObserver = new ResizeObserver((entries) => {
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

    paneRefs.current.forEach((el) => resizeObserver.observe(el));

    return () => resizeObserver.disconnect();
  }, [indicatorConfigs, theme, currentTheme, mainChart]);

  // Update Data
  useEffect(() => {
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
  }, [indicatorResults, indicatorConfigs, currentTheme]);

  const visiblePaneConfigs = indicatorConfigs.filter((i) => i.visible && i.indicatorType === "pane");

  return (
    <>
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
    </>
  );
}
