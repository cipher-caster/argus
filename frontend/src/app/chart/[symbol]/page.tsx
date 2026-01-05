"use client";

/**
 * Chart Page - /chart/[symbol]
 * Interactive chart view for a specific symbol
 */

import { CandlestickChart } from "@/components/CandlestickChart";
import { IndicatorToolbar } from "@/components/IndicatorToolbar";
import { ThemeToggle } from "@/components/ThemeToggle";
import { TimeframeSelector } from "@/components/TimeframeSelector";
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
  // Convert URL format (BTC-USDT) to API format (BTC/USDT)
  const symbol = params.symbol.replace("-", "/");

  const [timeframe, setTimeframe] = useState("1h");

  // Fetch market data
  const ohlcvQuery = useOHLCV(symbol, timeframe, 1000);
  const { data: ohlcvData, isLoading: isLoadingOHLCV, fetchNextPage, hasNextPage, isFetchingNextPage } = ohlcvQuery;

  // Debug: Log the actual query state
  console.log("[Page] ohlcvQuery state:", {
    hasNextPage,
    isFetchingNextPage,
    pagesCount: ohlcvData?.pages?.length,
    pageParams: ohlcvData?.pageParams,
  });

  const tickerQuery = useTicker(symbol);
  const providerQuery = useProvider();
  const tickerData = tickerQuery.data;
  const providerData = providerQuery.data;

  // Fetch indicator data
  useAvailableIndicators();
  const indicators = useIndicatorStore((s) => s.indicators);
  const { data: indicatorData, isLoading: isLoadingIndicators } = useCalculatedIndicators(symbol, timeframe);

  // Flatten candles from all pages
  const allCandles = ohlcvData?.pages.flatMap((page: { candles: any[] }) => page.candles) || [];
  // Sort by timestamp asc (older -> newer) just in case, though API returns desc usually we need to check API.
  // API market.py returns sorted by timestamp ASC at the end.
  // But infinite query prepends older pages?
  // No, pages are appended in the array [page1(latest), page2(older)...]
  // So we need to reverse the pages order or just sort all candles.
  const sortedCandles = [...allCandles].sort((a, b) => a.timestamp - b.timestamp);

  const currentPrice = tickerData?.price;
  const priceChange = sortedCandles.length ? (currentPrice ?? 0) - sortedCandles[sortedCandles.length - 1].close : 0; // compare with latest close? or 24h ago?
  // Usually price change is 24h. OHLCV might not have 24h ago exactly if 1h timeframe and only 100 loaded.
  // For now let's use the first candle of the *latest loaded* set?
  // Let's just use the oldest loaded candle for simple diff if we want "change since start of chart"
  // or better, rely on ticker data for 24h change if available.
  // But here we used ohlcvData[0] before.
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
            <span className="symbol-name">{symbol}</span>
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
          <TimeframeSelector selected={timeframe} onChange={setTimeframe} />
          <ThemeToggle />
          <span className="provider-badge">{providerData?.provider?.toUpperCase() || "BINANCE"}</span>
        </div>
      </header>

      {/* Chart Area */}
      <main className="main">
        <div className="chart-layout">
          <div className="toolbar-container">
            <IndicatorToolbar />
          </div>
          <div className="chart-area">
            <CandlestickChart
              candles={sortedCandles}
              symbol={symbol}
              isLoading={isLoadingOHLCV || isLoadingIndicators}
              indicatorResults={indicatorData?.results || []}
              indicatorConfigs={indicators}
              onLoadMore={() => {
                console.log(`[Page] onLoadMore called. hasNextPage=${hasNextPage}, isFetchingNextPage=${isFetchingNextPage}`);
                if (hasNextPage && !isFetchingNextPage) {
                  console.log("[Page] Calling fetchNextPage...");
                  fetchNextPage();
                }
              }}
              isLoadingMore={isFetchingNextPage}
            />
          </div>
        </div>
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
          padding: 12px 24px;
          background: var(--bg-secondary);
          border-bottom: 1px solid var(--border-color);
        }

        .header-left {
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .back-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 36px;
          height: 36px;
          background: var(--bg-tertiary);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          color: var(--text-secondary);
          text-decoration: none;
          transition: all 0.2s ease;
        }

        .back-btn:hover {
          background: var(--accent-primary);
          color: white;
        }

        .logo {
          display: flex;
          align-items: center;
          gap: 10px;
          font-size: 18px;
          font-weight: 700;
          color: var(--text-primary);
        }

        .logo-icon {
          color: var(--accent-primary);
          font-size: 20px;
        }

        .header-center {
          flex: 1;
          display: flex;
          justify-content: center;
        }

        .symbol-display {
          display: flex;
          align-items: baseline;
          gap: 16px;
        }

        .symbol-name {
          font-size: 20px;
          font-weight: 700;
          color: var(--text-primary);
        }

        .current-price {
          font-size: 24px;
          font-weight: 700;
          color: var(--text-primary);
        }

        .price-change {
          font-size: 16px;
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
          gap: 12px;
        }

        .provider-badge {
          padding: 8px 16px;
          background: var(--bg-tertiary);
          border: 1px solid var(--border-color);
          border-radius: 6px;
          font-size: 12px;
          font-weight: 600;
          letter-spacing: 1px;
          color: var(--text-secondary);
        }

        .main {
          flex: 1;
          display: flex;
          flex-direction: column;
          padding: 16px 24px;
          overflow: hidden;
        }

        .chart-layout {
          display: flex;
          flex: 1;
          gap: 16px;
          min-height: 0;
        }

        .toolbar-container {
          flex-shrink: 0;
        }

        .chart-area {
          flex: 1;
          min-width: 0;
          border-radius: 12px;
          overflow: hidden;
        }
      `}</style>
    </div>
  );
}
