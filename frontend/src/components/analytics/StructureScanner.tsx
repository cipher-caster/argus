"use client";

import { useToast } from "@/components/ui/toaster";
import { useCoinMeta } from "@/hooks/useCoinMeta";
import { fetchStructure, StructureResponse } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";
import { ArrowDown, ArrowUp, Ban, BoxSelect, RefreshCcw, Wallet } from "lucide-react";
import Link from "next/link";
import { CoinIcon } from "../features/dashboard/CoinIcon";

export function StructureScanner() {
  const { coinMeta } = useCoinMeta();
  const { toast, dismiss } = useToast();
  const { data, isLoading, error, refetch, isRefetching } = useQuery<StructureResponse>({
    queryKey: ["structure"],
    queryFn: () => fetchStructure(50),
    refetchInterval: 60000,
  });

  const handleRefresh = async () => {
    const id = toast("Refreshing weekly structure...", "info");
    await refetch();
    dismiss(id);
    toast("Weekly structure updated", "success");
  };

  if (isLoading) return <div className="p-10 text-center animate-pulse">Scanning Weekly Structure...</div>;
  if (error) return <div className="p-10 text-center text-red-500">Failed to load Structure</div>;
  if (!data) return null;

  // ... (color and icon helpers remain same) ...
  const getStatusColor = (status: string) => {
    switch (status) {
      case "BREAKOUT_UP":
        return "text-green-500 bg-green-500/10 border-green-500/20";
      case "BREAKOUT_DOWN":
        return "text-red-500 bg-red-500/10 border-red-500/20";
      case "FAKEOUT_LOW":
        return "text-blue-500 bg-blue-500/10 border-blue-500/20";
      default:
        return "text-muted-foreground bg-secondary/50 border-transparent";
    }
  };

  // Group data
  const breakouts = data.data.filter((i) => i.status === "BREAKOUT_UP");
  const breakdowns = data.data.filter((i) => i.status === "BREAKOUT_DOWN");
  const fakeouts = data.data.filter((i) => i.status === "FAKEOUT_LOW");
  const trapped = data.data.filter((i) => i.status === "TRAPPED");

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <BoxSelect className="text-primary" />
          The Weekly Trap (Monday Range)
          <button onClick={handleRefresh} disabled={isRefetching} className="hover:text-primary transition-colors ml-2 disabled:opacity-50" title="Refresh">
            <RefreshCcw size={16} className={isRefetching ? "animate-spin" : ""} />
          </button>
        </h2>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          {data.last_updated && <span>Updated: {new Date(data.last_updated).toLocaleTimeString()}</span>}
          <span className="border-l border-border pl-2">Scanned {data.data.length} assets</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Actionable */}
        <div className="space-y-6">
          {/* Breakouts UP */}
          <div className="bg-secondary/20 border border-border/50 rounded-xl p-4">
            <h3 className="text-sm font-bold text-green-500 mb-3 flex items-center gap-2">
              <ArrowUp size={16} /> WEEKLY BREAKOUTS (BULL)
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {breakouts.length === 0 && <span className="text-xs text-muted-foreground">No breakouts yet.</span>}
              {breakouts.map((item) => (
                <StructureCard key={item.symbol} item={item} coinMeta={coinMeta} />
              ))}
            </div>
          </div>

          {/* Fakeouts (High Value) */}
          <div className="bg-secondary/20 border border-border/50 rounded-xl p-4">
            <h3 className="text-sm font-bold text-blue-500 mb-3 flex items-center gap-2">
              <Wallet size={16} /> FAKEOUTS & RECLAIMS (SMART MONEY)
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {fakeouts.length === 0 && <span className="text-xs text-muted-foreground">No fakeouts detected.</span>}
              {fakeouts.map((item) => (
                <StructureCard key={item.symbol} item={item} coinMeta={coinMeta} />
              ))}
            </div>
          </div>

          {/* Breakdowns */}
          <div className="bg-secondary/20 border border-border/50 rounded-xl p-4">
            <h3 className="text-sm font-bold text-red-500 mb-3 flex items-center gap-2">
              <ArrowDown size={16} /> WEEKLY BREAKDOWNS (BEAR)
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {breakdowns.length === 0 && <span className="text-xs text-muted-foreground">No breakdowns yet.</span>}
              {breakdowns.map((item) => (
                <StructureCard key={item.symbol} item={item} coinMeta={coinMeta} />
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: The Trap (Do not trade) */}
        <div className="bg-secondary/20 border border-border/50 rounded-xl p-4 h-full">
          <h3 className="text-sm font-bold text-muted-foreground mb-3 flex items-center gap-2">
            <Ban size={16} /> TRAPPED (INSIDE MONDAY RANGE)
          </h3>
          <p className="text-xs text-muted-foreground mb-4">
            These assets are chopping inside the Monday High/Low.
            <strong> DO NOT TRADE</strong> until they pick a direction.
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 max-h-[600px] overflow-y-auto pr-2 scrollbar-thin">
            {trapped.map((item) => (
              <Link href={`/chart/${item.symbol}`} key={item.symbol}>
                <div className="flex items-center gap-2 p-2 rounded hover:bg-white/5 border border-transparent hover:border-white/10 transition-colors cursor-pointer opacity-60 hover:opacity-100">
                  <CoinIcon symbol={item.symbol} coinMeta={coinMeta} size={20} />
                  <span className="text-xs font-mono">{item.symbol}</span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function StructureCard({ item, coinMeta }: { item: any; coinMeta: any }) {
  return (
    <Link href={`/chart/${item.symbol}`} className="block">
      <div className="bg-background/60 hover:bg-background p-3 rounded-lg border border-transparent hover:border-border transition-all flex items-center justify-between group cursor-pointer">
        <div className="flex items-center gap-2">
          <CoinIcon symbol={item.symbol} coinMeta={coinMeta} />
          <div>
            <div className="font-bold text-xs">{item.symbol}</div>
            <div className="text-[10px] opacity-70">Rng: {item.range_pct}%</div>
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs font-mono">{item.price}</div>
        </div>
      </div>
    </Link>
  );
}
