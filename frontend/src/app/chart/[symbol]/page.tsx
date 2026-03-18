"use client";

import { CandlestickChart } from "@/components/features/chart/CandlestickChart";
import { ChartSettingsModal } from "@/components/features/chart/ChartSettingsModal";
import { CoinSignalIntel } from "@/components/features/chart/CoinSignalIntel";
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
  const [timeframe, setTimeframe] = useState("4h");
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const scrollToLatestRef = useRef<(() => void) | null>(null);

  const ohlcvQuery = useOHLCV(symbol, timeframe, 1000);
  const { data: ohlcvData, isLoading: isLoadingOHLCV, fetchNextPage, hasNextPage, isFetchingNextPage } = ohlcvQuery;

  const tickerQuery = useTicker(symbol);
  const providerQuery = useProvider();
  const tickerData = tickerQuery.data;
  const providerData = providerQuery.data;

  const allCandles = ohlcvData?.pages.flatMap((page: { candles: any[] }) => page.candles) || [];
  const sortedCandles = [...allCandles].sort((a, b) => a.timestamp - b.timestamp);

  const totalCandles = allCandles.length;
  const indicatorLimit = Math.max(1000, totalCandles + 200);

  useAvailableIndicators();
  const indicators = useIndicatorStore((s) => s.indicators);
  const { data: indicatorData, isLoading: isLoadingIndicators } = useCalculatedIndicators(symbol, timeframe, indicatorLimit);

  const currentPrice = tickerData?.price;
  const priceChangePercent = sortedCandles.length ? (((currentPrice ?? 0) - sortedCandles[0].close) / sortedCandles[0].close) * 100 : 0;

  const handleRefresh = async () => {
    await Promise.all([ohlcvQuery.refetch(), tickerQuery.refetch()]);
  };

  const isRefreshing = ohlcvQuery.isRefetching || tickerQuery.isRefetching;

  return (
    <div className="flex flex-col h-full bg-background overflow-hidden">
      <main className="flex-1 grid grid-cols-[1fr_280px] overflow-hidden">
        {/* Center: Chart */}
        <div className="overflow-hidden h-full min-h-0 relative flex flex-col">
          <CandlestickChart
            candles={sortedCandles}
            symbol={symbol}
            isLoading={isLoadingOHLCV || isLoadingIndicators}
            indicatorResults={indicatorData?.results || []}
            indicatorConfigs={indicators}
            onLoadMore={() => {
              if (hasNextPage && !isFetchingNextPage) fetchNextPage();
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

        {/* Right: Watchlist + Coin Signal Panel */}
        <aside className="bg-secondary border-l border-border flex flex-col overflow-hidden overflow-y-auto scrollbar-thin scrollbar-thumb-muted">
          <WatchlistPanel currentSymbol={symbol} />
          <CoinDetailsPanel symbol={symbol} timeframe={timeframe} />
          <CoinSignalIntel symbol={symbol} currentPrice={currentPrice ?? undefined} />
        </aside>
      </main>
    </div>
  );
}
