import { CoinInfo } from "@/lib/marketApi";
import { memo } from "react";
import { Sparkline } from "./Sparkline";

interface StatsCardsProps {
  coins: CoinInfo[];
  isLoading: boolean;
}

function StatsCardsComponent({ coins, isLoading }: StatsCardsProps) {
  // Generate a mock trend for visualization
  const getMockTrend = (trend: number | null) => {
    const base = 50;
    const count = 10;
    const vals = [base];
    for (let i = 1; i < count; i++) {
      const change = (Math.random() - 0.5) * 5 + (trend || 0) / count;
      vals.push(vals[i - 1] + change);
    }
    return vals;
  };

  // Calculate stats from available coins
  const totalVolume = coins.reduce((acc, coin) => acc + (coin.volume_24h || 0), 0);

  const topGainer = [...coins].sort((a, b) => (b.change_24h || 0) - (a.change_24h || 0))[0];
  const topLoser = [...coins].sort((a, b) => (a.change_24h || 0) - (b.change_24h || 0))[0];

  // Find highest volume coin (usually BTC)
  const volLeader = [...coins].sort((a, b) => (b.volume_24h || 0) - (a.volume_24h || 0))[0];

  const formatCurrency = (val: number) => {
    if (val >= 1e9) return `$${(val / 1e9).toFixed(2)}B`;
    if (val >= 1e6) return `$${(val / 1e6).toFixed(2)}M`;
    return `$${val.toLocaleString()}`;
  };

  const formatPercent = (val: number | null) => {
    if (val === null) return "-";
    return `${val >= 0 ? "+" : ""}${val.toFixed(2)}%`;
  };

  const StatCard = ({ title, value, subValue, trend, chartColor }: any) => (
    <div className="stat-card">
      <div className="stat-header">
        <span className="stat-title">{title}</span>
        {trend !== null && <span className={`stat-trend ${trend >= 0 ? "positive" : "negative"}`}>{formatPercent(trend)}</span>}
      </div>
      <div className="stat-content">
        <div className="stat-main">
          <span className="stat-value">{value}</span>
          <span className="stat-sub">{subValue}</span>
        </div>
        <div className="mini-chart">
          <Sparkline data={getMockTrend(trend)} width={80} height={30} color={chartColor} />
        </div>
      </div>
      <style jsx>{`
        .stat-card {
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 12px;
          padding: 16px;
          flex: 1;
          min-width: 240px;
        }
        .stat-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 12px;
        }
        .stat-title {
          font-size: 13px;
          color: var(--text-muted);
          font-weight: 500;
        }
        .stat-trend {
          font-size: 12px;
          font-weight: 600;
        }
        .stat-trend.positive {
          color: var(--success);
        }
        .stat-trend.negative {
          color: var(--danger);
        }

        .stat-content {
          display: flex;
          justify-content: space-between;
          align-items: flex-end;
        }
        .stat-main {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .stat-value {
          font-size: 18px;
          font-weight: 700;
          color: var(--text-primary);
        }
        .stat-sub {
          font-size: 12px;
          color: var(--text-secondary);
        }
        .mini-chart {
          width: 80px;
          height: 30px;
          opacity: 0.8;
        }
      `}</style>
    </div>
  );

  if (isLoading || coins.length === 0) {
    return (
      <div className="stats-grid">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="stat-card skeleton-card"></div>
        ))}
        <style jsx>{`
          .stats-grid {
            display: flex;
            gap: 16px;
            margin-bottom: 24px;
            flex-wrap: wrap;
          }
          .stat-card {
            height: 100px;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            flex: 1;
            min-width: 240px;
          }
          .skeleton-card {
            animation: pulse 1.5s infinite;
          }
          @keyframes pulse {
            0% {
              opacity: 0.6;
            }
            50% {
              opacity: 1;
            }
            100% {
              opacity: 0.6;
            }
          }
        `}</style>
      </div>
    );
  }

  return (
    <div className="stats-grid">
      <StatCard title="24h Volume (Top 50)" value={formatCurrency(totalVolume)} subValue="Global Market Activity" trend={null} chartColor="var(--accent-primary)" />
      <StatCard title="Top Gainer" value={topGainer?.symbol} subValue={formatCurrency(topGainer?.price || 0)} trend={topGainer?.change_24h} chartColor="var(--success)" />
      <StatCard title="Top Loser" value={topLoser?.symbol} subValue={formatCurrency(topLoser?.price || 0)} trend={topLoser?.change_24h} chartColor="var(--danger)" />
      <StatCard title="Vol Leader" value={volLeader?.symbol} subValue={formatCurrency(volLeader?.volume_24h || 0)} trend={volLeader?.change_24h} chartColor="#f59e0b" />

      <style jsx>{`
        .stats-grid {
          display: flex;
          gap: 16px;
          margin-bottom: 24px;
          flex-wrap: wrap;
        }
      `}</style>
    </div>
  );
}

export const StatsCards = memo(StatsCardsComponent);
