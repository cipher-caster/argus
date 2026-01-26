"use client";

import { Candle } from "@/lib/api";
import { IndicatorResult } from "@/lib/indicatorApi";
import { IndicatorConfig } from "@/stores/indicatorStore";
import { memo, useState } from "react";
import { ChartCanvas } from "./components/ChartCanvas";
import { ChartHeader } from "./components/ChartHeader";
import { ChartIndicators } from "./components/ChartIndicators";
import { ChartPanes } from "./components/ChartPanes";
import { MainChartSeries } from "./components/MainChartSeries";
import { OracleMarkers } from "./components/OracleMarkers";
import { StrategyOraclePanel } from "./components/StrategyOraclePanel";
import { ChartProvider, useChart } from "./context/ChartContext";
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
  scrollToLatestRef?: React.MutableRefObject<(() => void) | null>;
  price?: number;
  priceChangePercent?: number;
  provider?: string;
  onOpenSettings?: () => void;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

function CandlestickChartComponent({
  candles,
  symbol,
  isLoading,
  indicatorResults = [],
  indicatorConfigs = [],
  onLoadMore,
  isLoadingMore,
  timeframe = "1h",
  onTimeframeChange,
  scrollToLatestRef,
  price,
  priceChangePercent,
  provider,
  onOpenSettings,
  onRefresh,
  isRefreshing,
}: CandlestickChartProps) {
  const [isIndicatorModalOpen, setIsIndicatorModalOpen] = useState(false);
  const [editingIndicator, setEditingIndicator] = useState<IndicatorConfig | null>(null);

  // Check active strategy
  const activeStrategy = indicatorConfigs.find((i) => i.type === "prophet_strategy" && i.visible);

  // Loading State - Use Skeleton
  if (isLoading && candles.length === 0) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-card rounded-xl border border-border shadow-inner">
        <div className="flex items-center gap-2 text-muted-foreground">
          <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          Loading...
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full flex flex-col bg-card rounded-xl overflow-hidden border border-border shadow-inner">
      <ChartProvider>
        <ChartHeader
          symbol={symbol}
          price={price}
          priceChangePercent={priceChangePercent}
          provider={provider}
          onOpenSettings={onOpenSettings}
          onRefresh={onRefresh}
          isRefreshing={isRefreshing}
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

        {/* Main Chart Area */}
        <div className="flex-1 w-full relative min-h-[400px]">
          {activeStrategy && <StrategyOraclePanel symbol={symbol} timeframe={timeframe} />}
          <ChartCanvas className="absolute inset-0 w-full h-full">
            <MainChartSeries candles={candles} timeframe={timeframe} onLoadMore={onLoadMore} isLoadingMore={isLoadingMore} />
            {activeStrategy && <OracleMarkers symbol={symbol} timeframe={timeframe} />}
            <ChartIndicators indicatorResults={indicatorResults} indicatorConfigs={indicatorConfigs} />
            <ScrollToLatestRegistrar scrollToLatestRef={scrollToLatestRef} />

            {candles.length === 0 && !isLoading && (
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-10 bg-background/50">
                <span className="text-foreground text-lg font-bold">No chart data available</span>
              </div>
            )}
          </ChartCanvas>
        </div>

        {/* Pane Indicators */}
        <ChartPanes indicatorConfigs={indicatorConfigs} indicatorResults={indicatorResults} />
      </ChartProvider>

      <IndicatorModal isOpen={isIndicatorModalOpen} onClose={() => setIsIndicatorModalOpen(false)} editingIndicator={editingIndicator} />
    </div>
  );
}

// Sub-component to register scroll ref
function ScrollToLatestRegistrar({ scrollToLatestRef }: { scrollToLatestRef?: React.MutableRefObject<(() => void) | null> }) {
  const { chart } = useChart();

  // Register ref
  if (scrollToLatestRef && chart) {
    if (scrollToLatestRef.current === null || scrollToLatestRef.current.name !== "scrollToLatest") {
      const scrollToLatest = () => {
        chart.timeScale().scrollToPosition(0, true);
      };
      scrollToLatestRef.current = scrollToLatest;
    }
  }

  return null;
}

export const CandlestickChart = memo(CandlestickChartComponent);
