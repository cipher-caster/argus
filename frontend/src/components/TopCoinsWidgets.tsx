import { CoinInfo } from "@/lib/marketApi";
import Link from "next/link";
import { memo } from "react";

interface TopCoinsWidgetsProps {
  coins: CoinInfo[];
  isLoading: boolean;
}

function TopCoinsWidgetsComponent({ coins, isLoading }: TopCoinsWidgetsProps) {
  const getTopGainers = () => [...coins].sort((a, b) => (b.change_24h || 0) - (a.change_24h || 0)).slice(0, 5);
  const getTopLosers = () => [...coins].sort((a, b) => (a.change_24h || 0) - (b.change_24h || 0)).slice(0, 5);
  const getTopVolume = () => [...coins].sort((a, b) => (b.volume_24h || 0) - (a.volume_24h || 0)).slice(0, 5);

  const formatPrice = (val: number) => {
    if (val < 1) return val.toFixed(4);
    if (val < 10) return val.toFixed(3);
    return val.toLocaleString(undefined, { maximumFractionDigits: 2 });
  };

  const CoinList = ({ title, data, type }: { title: string; data: CoinInfo[]; type: "gain" | "loss" | "vol" }) => (
    <div className="widget">
      <div className="widget-header">
        <span className="widget-title">{title}</span>
        <span className="widget-more">More &gt;</span>
      </div>
      <div className="widget-list">
        {data.map((coin, i) => (
          <Link href={`/chart/${coin.symbol.replace("/", "-")}`} key={coin.symbol} className="widget-row">
            <div className="row-left">
              <span className="row-rank">{i + 1}</span>
              <div className="row-coin">
                <span className="coin-symbol">{coin.name}</span>
                <span className="coin-price">${formatPrice(coin.price)}</span>
              </div>
            </div>
            <div className={`row-change ${type === "gain" ? "positive" : type === "loss" ? "negative" : ""}`}>
              {type === "vol" ? `$${(coin.volume_24h! / 1e6).toFixed(0)}M` : `${(coin.change_24h || 0) > 0 ? "+" : ""}${(coin.change_24h || 0).toFixed(2)}%`}
            </div>
          </Link>
        ))}
      </div>
      <style jsx>{`
        .widget {
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 12px;
          padding: 16px;
          flex: 1;
          min-width: 300px;
        }
        .widget-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 12px;
          font-size: 14px;
          font-weight: 600;
        }
        .widget-more {
          font-size: 12px;
          color: var(--text-secondary);
          cursor: pointer;
        }
        .widget-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        .widget-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px 0;
          border-bottom: 1px solid var(--border-color);
          text-decoration: none;
          color: inherit;
          transition: background 0.2s;
        }
        .widget-row:hover {
          background: var(--bg-tertiary);
          padding-left: 4px;
          padding-right: 4px;
          border-radius: 4px;
        }
        .widget-row:last-child {
          border-bottom: none;
        }

        .row-left {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .row-rank {
          width: 20px;
          font-size: 12px;
          color: var(--text-muted);
          font-weight: 600;
        }
        .row-coin {
          display: flex;
          flex-direction: column;
        }
        .coin-symbol {
          font-size: 13px;
          font-weight: 700;
        }
        .coin-price {
          font-size: 12px;
          color: var(--text-secondary);
        }

        .row-change {
          font-size: 13px;
          font-weight: 600;
        }
        .row-change.positive {
          color: var(--success);
        }
        .row-change.negative {
          color: var(--danger);
        }
      `}</style>
    </div>
  );

  if (isLoading)
    return (
      <div className="widgets-grid">
        <div className="widget skeleton"></div>
      </div>
    );

  return (
    <div className="widgets-grid">
      <CoinList title="Top Gainers" data={getTopGainers()} type="gain" />
      <CoinList title="Top Losers" data={getTopLosers()} type="loss" />
      <CoinList title="Volume Leaders" data={getTopVolume()} type="vol" />

      <style jsx>{`
        .widgets-grid {
          display: flex;
          gap: 16px;
          margin-bottom: 32px;
          flex-wrap: wrap;
        }
        .skeleton {
          height: 300px;
          animation: pulse 1.5s infinite;
          background: var(--bg-secondary);
          border-radius: 12px;
        }
      `}</style>
    </div>
  );
}

export const TopCoinsWidgets = memo(TopCoinsWidgetsComponent);
