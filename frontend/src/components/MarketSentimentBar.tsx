"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toaster";
import { cn } from "@/lib/utils";
import { Moon, RefreshCcw, Waves, Zap } from "lucide-react";

interface MarketSentimentData {
  bullish_pct: number;
  bearish_pct: number;
  sleeping_pct?: number; // Optional for Confluence
  market_state?: string; // Optional for Oracle (STRONG BULL, STRONG BEAR, etc.)
  verdict?: string; // Optional for Confluence (TSUNAMI_BULL, TSUNAMI_BEAR, etc.)
  top_signals?: string[]; // Optional for Oracle
}

interface MarketSentimentBarProps {
  data: MarketSentimentData | undefined;
  isLoading: boolean;
  isRefetching: boolean;
  onRefresh: () => Promise<void>;
  error?: Error | null;
  variant?: "confluence" | "oracle"; // Determines which style/labels to use
}

export function MarketSentimentBar({ data, isLoading, isRefetching, onRefresh, error, variant = "oracle" }: MarketSentimentBarProps) {
  const { toast, dismiss } = useToast();

  const handleRefresh = async () => {
    const id = toast("Refreshing market sentiment...", "info");
    try {
      await onRefresh();
    } catch (e) {
      // Ignore refetch errors, they're handled by error boundary
    }
    dismiss(id);
    toast("Market sentiment updated", "success");
  };

  if (isLoading) return <Skeleton className="h-12 rounded-lg" />;
  if (error) return <div className="h-12 flex items-center justify-center bg-secondary/30 border border-red-500/20 text-red-500 rounded-lg italic text-xs px-4">Market Sentiment Unavailable</div>;
  if (!data) return <Skeleton className="h-12 rounded-lg" />;

  // Determine market state and visuals
  const getMarketVisuals = () => {
    if (variant === "confluence") {
      const verdict = data.verdict || "";
      switch (verdict) {
        case "SLEEPING":
          return { icon: Moon, color: "text-blue-400", bg: "bg-blue-500/10", label: "MARKET SLEEPING", desc: "Low Volatility. Stay Cash." };
        case "TSUNAMI_BULL":
          return { icon: Waves, color: "text-green-500", bg: "bg-green-500/10", label: "BULL TSUNAMI", desc: "Aggressive Longs Allowed." };
        case "TSUNAMI_BEAR":
          return { icon: Waves, color: "text-red-500", bg: "bg-red-500/10", label: "BEAR TSUNAMI", desc: "Aggressive Shorts Allowed." };
        default:
          return { icon: Zap, color: "text-yellow-500", bg: "bg-yellow-500/10", label: "CHOPPY / VOLATILE", desc: "Reduce Position Size." };
      }
    } else {
      // Oracle variant
      const marketState = data.market_state || "Analyzing";
      const labelColor = marketState === "STRONG BULL" ? "text-green-400" : marketState === "STRONG BEAR" ? "text-red-400" : "text-cyan-400";
      const bgColor = marketState === "STRONG BULL" ? "bg-green-500/10" : marketState === "STRONG BEAR" ? "bg-red-500/10" : "bg-cyan-500/10";

      return { icon: Zap, color: labelColor, bg: bgColor, label: marketState.toUpperCase(), desc: "Oracle Market Intelligence" };
    }
  };

  const visuals = getMarketVisuals();
  const Icon = visuals.icon;
  const confidence = Math.max(data.bullish_pct, data.bearish_pct);

  return (
    <div className={cn("bg-secondary/30 rounded-lg px-4 py-3 border border-border/50 backdrop-blur-sm flex items-center justify-between gap-8", visuals.bg)}>
      {/* Left: Market State */}
      <div className="flex items-center gap-4">
        <div className={cn("p-3 rounded-xl bg-background/50 border border-border/50", visuals.color)}>
          <Icon size={18} />
        </div>
        <div>
          <div className="text-[10px] text-muted-foreground font-bold uppercase tracking-wide">{variant === "confluence" ? "Market Confluence" : "Oracle Intelligence"}</div>
          <div className={cn("text-sm font-black uppercase tracking-tight", visuals.color)}>{visuals.label}</div>
        </div>
      </div>

      {/* Center: Metrics */}
      <div className="flex items-center gap-4">
        <div className="text-center">
          <div className={cn("text-xl font-black", visuals.color)}>{confidence}%</div>
          <div className="text-[9px] text-muted-foreground uppercase tracking-wider">Confidence</div>
        </div>
        <div className="h-8 w-px bg-border/50" />
        <div className="flex items-center gap-2 text-[10px] font-bold uppercase">
          <span className="text-green-500">{data.bullish_pct}% Bull</span>
          <span className="text-muted-foreground">/</span>
          <span className="text-red-500">{data.bearish_pct}% Bear</span>
          {data.sleeping_pct !== undefined && (
            <>
              <span className="text-muted-foreground">/</span>
              <span className="text-blue-400">{data.sleeping_pct}% Sleep</span>
            </>
          )}
        </div>
      </div>

      {/* Right: Top Signals or Progress Bar */}
      <div className="flex items-center gap-3">
        {variant === "oracle" && data.top_signals && data.top_signals.length > 0 ? (
          <>
            {(() => {
              const longs: string[] = [];
              const shorts: string[] = [];

              data.top_signals.slice(0, 4).forEach((sig: string) => {
                const parts = sig.split(" ");
                const ticker = parts[0].replace("/USDT", "");
                const scorePart = parts[1] || "";

                if (scorePart.startsWith("-")) {
                  shorts.push(ticker);
                } else {
                  longs.push(ticker);
                }
              });

              return (
                <div className="flex items-center gap-2">
                  {longs.length > 0 && (
                    <div className="flex items-center gap-1">
                      <span className="text-[9px] text-green-500 font-bold uppercase">L:</span>
                      {longs.slice(0, 2).map((ticker) => (
                        <span key={ticker} className="bg-background border border-green-500/30 px-1.5 py-0.5 rounded text-[9px] font-bold text-green-500">
                          {ticker}
                        </span>
                      ))}
                    </div>
                  )}
                  {shorts.length > 0 && (
                    <div className="flex items-center gap-1">
                      <span className="text-[9px] text-red-500 font-bold uppercase">S:</span>
                      {shorts.slice(0, 2).map((ticker) => (
                        <span key={ticker} className="bg-background border border-red-500/30 px-1.5 py-0.5 rounded text-[9px] font-bold text-red-500">
                          {ticker}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              );
            })()}
          </>
        ) : (
          <div className="w-48 space-y-1">
            <div className="h-3 w-full bg-background/50 rounded-full overflow-hidden flex border border-white/5">
              {data.sleeping_pct !== undefined && <div style={{ width: `${data.sleeping_pct}%` }} className="bg-blue-500/50 h-full" title={`Sleeping: ${data.sleeping_pct}%`} />}
              <div style={{ width: `${data.bullish_pct}%` }} className="bg-green-500 h-full" title={`Bullish: ${data.bullish_pct}%`} />
              <div style={{ width: `${data.bearish_pct}%` }} className="bg-red-500 h-full" title={`Bearish: ${data.bearish_pct}%`} />
            </div>
          </div>
        )}
        <button onClick={handleRefresh} disabled={isRefetching} className="p-1.5 rounded-md text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50" title="Refresh">
          <RefreshCcw size={14} className={cn(isRefetching && "animate-spin")} />
        </button>
      </div>
    </div>
  );
}
