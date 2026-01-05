"use client";

import { TrendingDown, TrendingUp } from "lucide-react";
import { useEffect, useState } from "react";

interface CoinDetailsPanelProps {
  symbol: string;
}

interface TickerDetails {
  symbol: string;
  price: number;
  change_24h: number;
  volume_24h: number;
  high_24h: number;
  low_24h: number;
}

export function CoinDetailsPanel({ symbol }: CoinDetailsPanelProps) {
  const [details, setDetails] = useState<TickerDetails | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    async function fetchDetails() {
      try {
        setLoading(true);
        const res = await fetch(`${apiUrl}/api/market/tickers`);
        if (!res.ok) return;
        const data = await res.json();
        const ticker = data.tickers?.find((t: TickerDetails) => t.symbol === symbol);
        if (ticker) {
          setDetails(ticker);
        }
      } catch (e) {
        console.error("Failed to fetch coin details", e);
      } finally {
        setLoading(false);
      }
    }

    fetchDetails();
    const interval = setInterval(fetchDetails, 10000);
    return () => clearInterval(interval);
  }, [symbol]);

  if (loading && !details) {
    return (
      <div className="coin-details-panel">
        <div className="loading-skeleton">Loading...</div>
        <style jsx>{styles}</style>
      </div>
    );
  }

  if (!details) {
    return (
      <div className="coin-details-panel">
        <div className="no-data">No data available</div>
        <style jsx>{styles}</style>
      </div>
    );
  }

  const isPositive = (details.change_24h || 0) >= 0;
  const priceRange = details.high_24h - details.low_24h;
  const currentPosition = priceRange > 0 ? ((details.price - details.low_24h) / priceRange) * 100 : 50;

  return (
    <div className="coin-details-panel">
      {/* Header */}
      <div className="details-header">
        <div className="coin-symbol">{symbol.replace("/USDT", "")}</div>
        <div className="coin-pair">{symbol}</div>
      </div>

      {/* Price */}
      <div className="price-section">
        <div className="current-price">${details.price?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 6 })}</div>
        <div className={`price-change ${isPositive ? "positive" : "negative"}`}>
          {isPositive ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
          <span>
            {isPositive ? "+" : ""}
            {details.change_24h?.toFixed(2)}%
          </span>
        </div>
      </div>

      {/* Key Stats */}
      <div className="stats-section">
        <div className="section-title">Key Stats (24H)</div>

        <div className="stat-row">
          <span className="stat-label">Volume</span>
          <span className="stat-value">{formatVolume(details.volume_24h)}</span>
        </div>

        <div className="stat-row">
          <span className="stat-label">High</span>
          <span className="stat-value">${details.high_24h?.toLocaleString(undefined, { maximumFractionDigits: 6 })}</span>
        </div>

        <div className="stat-row">
          <span className="stat-label">Low</span>
          <span className="stat-value">${details.low_24h?.toLocaleString(undefined, { maximumFractionDigits: 6 })}</span>
        </div>

        <div className="stat-row">
          <span className="stat-label">Range</span>
          <span className="stat-value">${priceRange.toLocaleString(undefined, { maximumFractionDigits: 6 })}</span>
        </div>
      </div>

      {/* Price Position Bar */}
      <div className="range-section">
        <div className="section-title">24H Price Position</div>
        <div className="range-bar">
          <div className="range-fill" style={{ width: `${currentPosition}%` }}></div>
          <div className="range-indicator" style={{ left: `${currentPosition}%` }}></div>
        </div>
        <div className="range-labels">
          <span className="range-low">${details.low_24h?.toLocaleString(undefined, { maximumFractionDigits: 2 })}</span>
          <span className="range-high">${details.high_24h?.toLocaleString(undefined, { maximumFractionDigits: 2 })}</span>
        </div>
      </div>

      {/* Performance */}
      <div className="performance-section">
        <div className="section-title">Performance</div>
        <div className="performance-grid">
          <div className={`perf-box ${isPositive ? "positive" : "negative"}`}>
            <div className="perf-value">
              {isPositive ? "+" : ""}
              {details.change_24h?.toFixed(2)}%
            </div>
            <div className="perf-label">24H</div>
          </div>
        </div>
      </div>

      <style jsx>{styles}</style>
    </div>
  );
}

function formatVolume(volume: number): string {
  if (!volume) return "—";
  if (volume >= 1_000_000_000) return `$${(volume / 1_000_000_000).toFixed(2)}B`;
  if (volume >= 1_000_000) return `$${(volume / 1_000_000).toFixed(2)}M`;
  if (volume >= 1_000) return `$${(volume / 1_000).toFixed(2)}K`;
  return `$${volume.toFixed(2)}`;
}

const styles = `
  .coin-details-panel {
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    border-top: 1px solid var(--border-color);
    background: var(--bg-secondary);
  }

  .loading-skeleton,
  .no-data {
    padding: 24px;
    text-align: center;
    color: var(--text-muted);
    font-size: 12px;
  }

  .details-header {
    display: flex;
    align-items: baseline;
    gap: 8px;
  }

  .coin-symbol {
    font-size: 18px;
    font-weight: 700;
    color: var(--text-primary);
  }

  .coin-pair {
    font-size: 12px;
    color: var(--text-muted);
  }

  .price-section {
    display: flex;
    align-items: baseline;
    gap: 12px;
  }

  .current-price {
    font-size: 24px;
    font-weight: 700;
    color: var(--text-primary);
  }

  .price-change {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 14px;
    font-weight: 600;
    padding: 4px 8px;
    border-radius: 6px;
  }

  .price-change.positive {
    color: var(--positive);
    background: rgba(34, 197, 94, 0.1);
  }

  .price-change.negative {
    color: var(--negative);
    background: rgba(239, 68, 68, 0.1);
  }

  .stats-section,
  .range-section,
  .performance-section {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .section-title {
    font-size: 11px;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
  }

  .stat-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .stat-label {
    font-size: 13px;
    color: var(--text-secondary);
  }

  .stat-value {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-primary);
  }

  .range-bar {
    height: 6px;
    background: var(--bg-tertiary);
    border-radius: 3px;
    position: relative;
    overflow: hidden;
  }

  .range-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--negative), var(--positive));
    border-radius: 3px;
  }

  .range-indicator {
    position: absolute;
    top: 50%;
    width: 12px;
    height: 12px;
    background: var(--text-primary);
    border: 2px solid var(--bg-secondary);
    border-radius: 50%;
    transform: translate(-50%, -50%);
  }

  .range-labels {
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    color: var(--text-muted);
  }

  .performance-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
  }

  .perf-box {
    padding: 12px;
    border-radius: 8px;
    text-align: center;
  }

  .perf-box.positive {
    background: rgba(34, 197, 94, 0.1);
  }

  .perf-box.negative {
    background: rgba(239, 68, 68, 0.1);
  }

  .perf-value {
    font-size: 14px;
    font-weight: 700;
  }

  .perf-box.positive .perf-value {
    color: var(--positive);
  }

  .perf-box.negative .perf-value {
    color: var(--negative);
  }

  .perf-label {
    font-size: 11px;
    color: var(--text-muted);
    margin-top: 4px;
  }
`;
