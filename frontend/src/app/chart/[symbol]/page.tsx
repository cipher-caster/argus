"use client";

/**
 * Chart Page - /chart/[symbol]
 * TradingView-style interactive chart with drawing tools and watchlist
 */

import { CandlestickChart } from "@/components/features/chart/CandlestickChart";
import { ChartSettingsModal } from "@/components/features/chart/ChartSettingsModal";
import { DrawingToolbar } from "@/components/features/chart/DrawingToolbar";
import { CoinDetailsPanel } from "@/components/features/dashboard/CoinDetailsPanel";
import { WatchlistPanel } from "@/components/features/dashboard/WatchlistPanel";
import { useAvailableIndicators, useCalculatedIndicators } from "@/hooks/useIndicators";
import { useOHLCV, useProvider, useTicker } from "@/hooks/useMarketData";
import { useIndicatorStore } from "@/stores/indicatorStore";
import { useRef, useState } from "react";

interface ChartPageProps {
  params: { symbol: string };
}

export default function ChartPage({ params }: ChartPageProps) {
  const symbol = params.symbol.replace("-", "/");
  const [timeframe, setTimeframe] = useState("1h");
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const scrollToLatestRef = useRef<(() => void) | null>(null);

  // Fetch market data
  const ohlcvQuery = useOHLCV(symbol, timeframe, 1000);
  const { data: ohlcvData, isLoading: isLoadingOHLCV, fetchNextPage, hasNextPage, isFetchingNextPage } = ohlcvQuery;

  const tickerQuery = useTicker(symbol);
  const providerQuery = useProvider();
  const tickerData = tickerQuery.data;
  const providerData = providerQuery.data;

  // Flatten candles first to know total count
  const allCandles = ohlcvData?.pages.flatMap((page: { candles: any[] }) => page.candles) || [];
  const sortedCandles = [...allCandles].sort((a, b) => a.timestamp - b.timestamp);

  // Fetch indicator data covering all loaded candles
  const totalCandles = allCandles.length;
  // Ensure we fetch enough data for indicators to stabilize (e.g. +200 for EMA200), but at least 1000 or current total
  const indicatorLimit = Math.max(1000, totalCandles + 200);

  useAvailableIndicators();
  const indicators = useIndicatorStore((s) => s.indicators);
  // Pass the dynamic limit based on loaded history
  const { data: indicatorData, isLoading: isLoadingIndicators } = useCalculatedIndicators(symbol, timeframe, indicatorLimit);

  const currentPrice = tickerData?.price;
  const priceChangePercent = sortedCandles.length ? (((currentPrice ?? 0) - sortedCandles[0].close) / sortedCandles[0].close) * 100 : 0;

  const handleRefresh = async () => {
    await Promise.all([ohlcvQuery.refetch(), tickerQuery.refetch()]);
  };

  const isRefreshing = ohlcvQuery.isRefetching || tickerQuery.isRefetching;

  return (
    <div className="flex flex-col h-full bg-background overflow-hidden">
      {/* Main Content - 3 Column Grid */}
      <main className="flex-1 grid grid-cols-[48px_1fr_280px] overflow-hidden">
        {/* Left: Drawing Tools */}
        <aside className="bg-secondary border-r border-border">
          <DrawingToolbar onScrollToLatest={() => scrollToLatestRef.current?.()} />
        </aside>

        {/* Center: Chart */}
        <div className="overflow-hidden h-full min-h-0 relative flex flex-col">
          <CandlestickChart
            candles={sortedCandles}
            symbol={symbol}
            isLoading={isLoadingOHLCV || isLoadingIndicators}
            indicatorResults={indicatorData?.results || []}
            indicatorConfigs={indicators}
            onLoadMore={() => {
              if (hasNextPage && !isFetchingNextPage) {
                fetchNextPage();
              }
            }}
            isLoadingMore={isFetchingNextPage}
            timeframe={timeframe}
            onTimeframeChange={setTimeframe}
            scrollToLatestRef={scrollToLatestRef}
            price={currentPrice ?? undefined}
            priceChangePercent={priceChangePercent}
            provider={providerData?.provider}
            onOpenSettings={() => setIsSettingsOpen(true)}
            onRefresh={handleRefresh}
            isRefreshing={isRefreshing}
          />
          <ChartSettingsModal isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
        </div>

        {/* Right: Watchlist + Coin Details */}
        <aside className="bg-secondary border-l border-border flex flex-col overflow-hidden">
          <WatchlistPanel currentSymbol={symbol} />
          <CoinDetailsPanel symbol={symbol} />
        </aside>
      </main>
    </div>
  );
}
