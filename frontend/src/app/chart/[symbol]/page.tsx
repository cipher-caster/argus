"use client";

/**
 * Chart Page - /chart/[symbol]
 * TradingView-style interactive chart with drawing tools and watchlist
 */

import { CandlestickChart } from "@/components/CandlestickChart";
import { DrawingToolbar } from "@/components/DrawingToolbar";
import { ThemeToggle } from "@/components/ThemeToggle";
import { WatchlistPanel } from "@/components/WatchlistPanel";
import { useAvailableIndicators, useCalculatedIndicators } from "@/hooks/useIndicators";
import { useOHLCV, useProvider, useTicker } from "@/hooks/useMarketData";
import { useIndicatorStore } from "@/stores/indicatorStore";
import { ChevronLeft, LayoutDashboard } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

interface ChartPageProps {
  params: { symbol: string };
}

export default function ChartPage({ params }: ChartPageProps) {
  const symbol = params.symbol.replace("-", "/");
  const [timeframe, setTimeframe] = useState("1h");

  // Fetch market data
  const ohlcvQuery = useOHLCV(symbol, timeframe, 1000);
  const { data: ohlcvData, isLoading: isLoadingOHLCV, fetchNextPage, hasNextPage, isFetchingNextPage } = ohlcvQuery;

  const tickerQuery = useTicker(symbol);
  const providerQuery = useProvider();
  const tickerData = tickerQuery.data;
  const providerData = providerQuery.data;

  // Fetch indicator data
  useAvailableIndicators();
  const indicators = useIndicatorStore((s) => s.indicators);
  const { data: indicatorData, isLoading: isLoadingIndicators } = useCalculatedIndicators(symbol, timeframe);

  // Flatten and sort candles
  const allCandles = ohlcvData?.pages.flatMap((page: { candles: any[] }) => page.candles) || [];
  const sortedCandles = [...allCandles].sort((a, b) => a.timestamp - b.timestamp);

  const currentPrice = tickerData?.price;
  const priceChangePercent = sortedCandles.length ? (((currentPrice ?? 0) - sortedCandles[0].close) / sortedCandles[0].close) * 100 : 0;

  return (
    <div className="chart-page">
      {/* Header */}
      <header className="header">
        <div className="header-left">
          <Link href="/" className="back-btn">
            <ChevronLeft size={20} />
          </Link>
          <h1 className="logo">
            <LayoutDashboard size={20} className="logo-icon" />
            Argus
          </h1>
        </div>

        <div className="header-center">
          <div className="symbol-display">
            {currentPrice && (
              <>
                <span className="current-price">${currentPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                <span className={`price-change ${priceChangePercent >= 0 ? "positive" : "negative"}`}>
                  {priceChangePercent >= 0 ? "+" : ""}
                  {priceChangePercent.toFixed(2)}%
                </span>
              </>
            )}
          </div>
        </div>

        <div className="header-right">
          <ThemeToggle />
          <span className="provider-badge">{providerData?.provider?.toUpperCase() || "BINANCE"}</span>
        </div>
      </header>

      {/* Main Content - 3 Column Grid */}
      <main className="main">
        {/* Left: Drawing Tools */}
        <aside className="left-sidebar">
          <DrawingToolbar />
        </aside>

        {/* Center: Chart */}
        <div className="chart-container">
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
          />
        </div>

        {/* Right: Watchlist */}
        <aside className="right-sidebar">
          <WatchlistPanel currentSymbol={symbol} />
        </aside>
      </main>

      <style jsx>{`
        .chart-page {
          display: flex;
          flex-direction: column;
          height: 100vh;
          background: var(--bg-primary);
        }

        .header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 8px 16px;
          background: var(--bg-secondary);
          border-bottom: 1px solid var(--border-color);
          gap: 16px;
        }

        .header-left {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .back-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 32px;
          height: 32px;
          background: var(--bg-tertiary);
          border: 1px solid var(--border-color);
          border-radius: 6px;
          color: var(--text-secondary);
          text-decoration: none;
          transition: all 0.15s;
        }

        .back-btn:hover {
          background: var(--accent-primary);
          color: white;
        }

        .logo {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 16px;
          font-weight: 700;
          color: var(--text-primary);
        }

        .header-center {
          flex: 1;
          display: flex;
          justify-content: center;
        }

        .symbol-display {
          display: flex;
          align-items: baseline;
          gap: 12px;
        }

        .symbol-name {
          font-size: 16px;
          font-weight: 700;
          color: var(--text-primary);
        }

        .current-price {
          font-size: 20px;
          font-weight: 700;
          color: var(--text-primary);
        }

        .price-change {
          font-size: 14px;
          font-weight: 600;
        }

        .price-change.positive {
          color: var(--success);
        }

        .price-change.negative {
          color: var(--danger);
        }

        .header-right {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .provider-badge {
          padding: 6px 12px;
          background: var(--bg-tertiary);
          border: 1px solid var(--border-color);
          border-radius: 6px;
          font-size: 11px;
          font-weight: 600;
          letter-spacing: 0.5px;
          color: var(--text-secondary);
        }

        .main {
          flex: 1;
          display: grid;
          grid-template-columns: 48px 1fr 280px;
          overflow: hidden;
        }

        .left-sidebar {
          background: var(--bg-secondary);
          border-right: 1px solid var(--border-color);
        }

        .chart-container {
          overflow: hidden;
        }

        .right-sidebar {
          background: var(--bg-secondary);
          border-left: 1px solid var(--border-color);
          overflow-y: auto;
        }
      `}</style>
    </div>
  );
}
