import { CoinIcon } from "@/components/features/dashboard/CoinIcon";
import { Skeleton } from "@/components/ui/skeleton";
import { useCoinMeta } from "@/hooks/useCoinMeta";
import { CoinInfo } from "@/lib/marketApi";
import Link from "next/link";
import { memo } from "react";

interface TopCoinsWidgetsProps {
  gainers: CoinInfo[];
  losers: CoinInfo[];
  volume: CoinInfo[];
  isLoading: boolean;
}

import { formatChange, formatPrice, formatVolume } from "@/lib/formatters";
import { cn } from "@/lib/utils";

function TopCoinsWidgetsComponent({ gainers, losers, volume, isLoading }: TopCoinsWidgetsProps) {
  const { coinMeta } = useCoinMeta();

  const CoinList = ({ title, data, type }: { title: string; data: CoinInfo[]; type: "gain" | "loss" | "vol" }) => (
    <div className="bg-secondary border border-border rounded-2xl p-5 flex-1 min-w-[320px] shadow-sm">
      <div className="flex justify-between items-center mb-6">
        <span className="text-[15px] font-extrabold text-foreground tracking-tight">{title}</span>
        <Link href={type === "gain" ? "/markets/gainers" : type === "loss" ? "/markets/losers" : "/markets/volume"} className="text-[12px] font-bold text-muted-foreground hover:text-primary transition-colors no-underline">
          View More &gt;
        </Link>
      </div>
      <div className="space-y-1">
        {data.map((coin, i) => {
          return (
            <Link href={`/chart/${coin.symbol.replace("/", "-")}`} key={coin.symbol} className="flex justify-between items-center p-2.5 rounded-xl transition-all duration-200 hover:bg-muted group no-underline text-inherit">
              <div className="flex items-center gap-3">
                <span className="w-5 text-[13px] font-bold text-muted-foreground text-center">{i + 1}</span>
                <div className="flex items-center gap-2">
                  <CoinIcon symbol={coin.symbol} coinMeta={coinMeta} size={20} />
                  <span className="text-[14px] font-bold text-foreground group-hover:text-primary transition-colors w-16 truncate">{coin.symbol.split("/")[0]}</span>
                  <span className="text-[13px] font-medium text-muted-foreground">${formatPrice(coin.price)}</span>
                </div>
              </div>
              <div className={cn("text-[14px] font-medium font-mono tracking-tight", type === "gain" ? "text-success" : type === "loss" ? "text-danger" : "text-foreground")}>
                {type === "vol" ? formatVolume(coin.volume_24h) : formatChange(coin.change_24h)}
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );

  if (isLoading)
    return (
      <div className="flex flex-wrap gap-4 mb-8">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-[280px] flex-1 min-w-[320px] rounded-2xl" />
        ))}
      </div>
    );

  return (
    <div className="flex flex-wrap gap-4 mb-8">
      <CoinList title="Top Gainers" data={gainers.slice(0, 3)} type="gain" />
      <CoinList title="Top Losers" data={losers.slice(0, 3)} type="loss" />
      <CoinList title="Volume Leaders" data={volume.slice(0, 3)} type="vol" />
    </div>
  );
}

export const TopCoinsWidgets = memo(TopCoinsWidgetsComponent);
