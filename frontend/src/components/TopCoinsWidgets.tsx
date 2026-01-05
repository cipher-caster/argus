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
        <Link href={`/markets/${type === "gain" ? "gainers" : type === "loss" ? "losers" : "volume"}`} className="widget-more">
          More &gt;
        </Link>
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
          padding: 20px;
          flex: 1;
          min-width: 320px;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }
        .widget-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
          font-size: 15px;
          font-weight: 700;
          color: var(--text-primary);
        }
        /* Link Styles Reset */
        .widget-list :global(a) {
          text-decoration: none !important;
          color: inherit !important;
        }

        div.widget-row {
          /* wrapper if needed, but Link is the container */
        }

        :global(.widget-row) {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 10px 8px;
          border-radius: 8px;
          transition: all 0.2s;
          text-decoration: none !important;
          color: var(--text-primary) !important;
        }

        :global(.widget-row:visited),
        :global(.widget-row:active),
        :global(.widget-row:focus) {
          color: var(--text-primary) !important;
          text-decoration: none !important;
        }

        :global(.widget-row:hover) {
          background: var(--bg-tertiary);
          text-decoration: none !important;
          color: var(--text-primary) !important;
        }

        /* More Link */
        :global(.widget-more) {
          font-size: 12px;
          color: var(--text-secondary) !important;
          cursor: pointer;
          transition: color 0.2s;
          text-decoration: none !important;
        }
        :global(.widget-more:hover) {
          color: var(--accent-primary) !important;
          text-decoration: none !important;
        }

        .row-left {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .row-rank {
          width: 24px;
          font-size: 13px;
          color: var(--text-muted);
          font-weight: 600;
          text-align: center;
        }
        .row-coin {
          display: flex;
          flex-direction: row;
          align-items: center;
          gap: 8px;
        }
        .coin-symbol {
          font-size: 14px;
          font-weight: 700;
          color: var(--text-primary);
          line-height: 1.2;
        }
        .coin-price {
          font-size: 13px;
          color: var(--text-secondary);
          font-weight: 500;
        }

        .row-change {
          font-size: 14px;
          font-weight: 600;
          text-align: right;
          min-width: 60px; /* Ensure strictly aligned column */
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
