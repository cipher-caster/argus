import { CoinInfo } from "@/lib/marketApi";
import Link from "next/link";
import { memo } from "react";

interface TopCoinsWidgetsProps {
  coins: CoinInfo[];
  isLoading: boolean;
}

import { cn } from "@/lib/utils";

function TopCoinsWidgetsComponent({ coins, isLoading }: TopCoinsWidgetsProps) {
  const getTopGainers = () => [...coins].sort((a, b) => (b.change_24h || 0) - (a.change_24h || 0)).slice(0, 5);
  const getTopLosers = () => [...coins].sort((a, b) => (a.change_24h || 0) - (b.change_24h || 0)).slice(0, 5);
  const getTopVolume = () => [...coins].sort((a, b) => (b.volume_24h || 0) - (a.volume_24h || 0)).slice(0, 5);

  const formatPrice = (val: number) => {
    if (val < 1) return val.toFixed(4);
    if (val < 10) return val.toFixed(3);
    return val.toLocaleString(undefined, { maximumFractionDigits: 2 });
  };

  const formatVolume = (vol: number | null) => {
    if (!vol) return "—";
    if (vol >= 1e9) return `$${(vol / 1e9).toFixed(2)}B`;
    if (vol >= 1e6) return `$${(vol / 1e6).toFixed(1)}M`;
    return `$${(vol / 1e3).toFixed(0)}K`;
  };

  const CoinList = ({ title, data, type }: { title: string; data: CoinInfo[]; type: "gain" | "loss" | "vol" }) => (
    <div className="bg-secondary border border-border rounded-2xl p-5 flex-1 min-w-[320px] shadow-sm">
      <div className="flex justify-between items-center mb-6">
        <span className="text-[15px] font-extrabold text-foreground tracking-tight">{title}</span>
        <Link href={`/markets/${type === "gain" ? "gainers" : type === "loss" ? "losers" : "volume"}`} className="text-[12px] font-bold text-muted-foreground hover:text-primary transition-colors no-underline">
          View More &gt;
        </Link>
      </div>
      <div className="space-y-1">
        {data.map((coin, i) => (
          <Link href={`/chart/${coin.symbol.replace("/", "-")}`} key={coin.symbol} className="flex justify-between items-center p-2.5 rounded-xl transition-all duration-200 hover:bg-muted group no-underline text-inherit">
            <div className="flex items-center gap-3">
              <span className="w-5 text-[13px] font-bold text-muted-foreground text-center">{i + 1}</span>
              <div className="flex items-center gap-2">
                <span className="text-[14px] font-bold text-foreground group-hover:text-primary transition-colors w-28 truncate">{coin.name}</span>
                <span className="text-[13px] font-medium text-muted-foreground">${formatPrice(coin.price)}</span>
              </div>
            </div>
            <div className={cn("text-[14px] font-bold font-mono tracking-tight", type === "gain" ? "text-success" : type === "loss" ? "text-danger" : "text-foreground")}>
              {type === "vol" ? formatVolume(coin.volume_24h) : `${(coin.change_24h || 0) > 0 ? "+" : ""}${(coin.change_24h || 0).toFixed(2)}%`}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );

  if (isLoading || coins.length === 0)
    return (
      <div className="flex flex-wrap gap-4 mb-8">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-[280px] bg-secondary border border-border rounded-2xl flex-1 min-w-[320px] animate-pulse" />
        ))}
      </div>
    );

  return (
    <div className="flex flex-wrap gap-4 mb-8">
      <CoinList title="Top Gainers" data={getTopGainers()} type="gain" />
      <CoinList title="Top Losers" data={getTopLosers()} type="loss" />
      <CoinList title="Volume Leaders" data={getTopVolume()} type="vol" />
    </div>
  );
}

export const TopCoinsWidgets = memo(TopCoinsWidgetsComponent);
