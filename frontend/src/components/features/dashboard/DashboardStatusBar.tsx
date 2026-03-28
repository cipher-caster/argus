"use client";

import { useMarketIndicators, DashboardIndicators } from "@/hooks/useMarketIndicators";
import { useRegime } from "@/hooks/useAnalyticsData";
import { useAlignedSetups } from "@/hooks/useAlignedSetups";
import { BestSetupItem, RegimeData } from "@/lib/api";
import { formatPriceCompact, formatVolume } from "@/lib/formatters";
import { cn } from "@/lib/utils";
import { useQueryClient } from "@tanstack/react-query";
import { RefreshCcw, TrendingDown, TrendingUp, X, Target, Clock } from "lucide-react";
import { useState } from "react";

function Divider() {
  return <div className="h-4 w-px bg-border/50 shrink-0" />;
}

function RegimeModal({ regime, indicators, onClose }: { regime: RegimeData | null; indicators: DashboardIndicators | undefined; onClose: () => void }) {
  const { aligned: alignedSetups, counter: counterSetups } = useAlignedSetups(regime?.regime);

  if (!regime) return null;

  const isBull = regime.regime === "BULL";
  const isBear = regime.regime === "BEAR";

  const rsi = indicators?.average_rsi?.value;
  const cap = indicators?.total_market_cap?.value;
  const dom = indicators?.btc_dominance?.value;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div
        className="bg-background border border-border rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className={cn(
          "flex items-center justify-between px-6 py-4 border-b sticky top-0 z-10",
          isBull ? "bg-green-500/10 border-green-500/20" : "bg-red-500/10 border-red-500/20",
          "bg-background"
        )}>
          <div className="flex items-center gap-3">
            {isBull ? <TrendingUp size={20} className="text-green-500" /> : <TrendingDown size={20} className="text-red-500" />}
            <div>
              <h2 className="text-lg font-black uppercase tracking-wider">{regime.regime} Market</h2>
              <p className="text-xs text-muted-foreground">BTC Weekly EMA50</p>
            </div>
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground transition-colors">
            <X size={18} />
          </button>
        </div>

        <div className="p-6 space-y-5">
          {/* So What — the actionable part */}
          <div className={cn(
            "rounded-xl p-4 space-y-3",
            isBear ? "bg-red-500/5 border border-red-500/20" : "bg-green-500/5 border border-green-500/20"
          )}>
            <h3 className="text-xs font-black uppercase tracking-widest text-muted-foreground flex items-center gap-1.5">
              <Target size={12} />
              So What — Where To Act
            </h3>
            {isBear ? (
              <div className="space-y-2 text-sm">
                <p>BTC at <strong>${formatPriceCompact(regime.btc_price)}</strong> is <strong className="text-red-500">{Math.abs(regime.distance_pct)}% below</strong> the bull line at <strong>${formatPriceCompact(regime.ema50)}</strong>.</p>
                <p>Trend is down. <strong>Short setups only</strong> right now. Don&apos;t buy spot and hold — you&apos;re fighting the trend.</p>
              </div>
            ) : (
              <div className="space-y-2 text-sm">
                <p>BTC at <strong>${formatPriceCompact(regime.btc_price)}</strong> is <strong className="text-green-500">+{regime.distance_pct}% above</strong> the bear line at <strong>${formatPriceCompact(regime.ema50)}</strong>.</p>
                <p>Trend is up. <strong>HODL BTC, long alts</strong>. Shorts are counter-trend — higher risk.</p>
              </div>
            )}
          </div>

          {/* What to wait for */}
          <div className="bg-muted/30 rounded-xl p-4 space-y-3">
            <h3 className="text-xs font-black uppercase tracking-widest text-muted-foreground flex items-center gap-1.5">
              <Clock size={12} />
              What To Wait For
            </h3>
            {isBear ? (
              <div className="space-y-2">
                <div className="flex items-center gap-3 p-2.5 rounded-lg bg-background border border-border/50">
                  <span className="text-green-500 font-black text-lg">↑</span>
                  <div>
                    <p className="text-sm font-bold">Bull regime starts</p>
                    <p className="text-xs text-muted-foreground">Weekly close above <strong className="text-foreground">${formatPriceCompact(regime.ema50)}</strong></p>
                  </div>
                </div>
                <p className="text-xs text-muted-foreground">Until then, only short. When BTC crosses above ${formatPriceCompact(regime.ema50)} on a weekly close, switch to longs.</p>
              </div>
            ) : (
              <div className="space-y-2">
                <div className="flex items-center gap-3 p-2.5 rounded-lg bg-background border border-border/50">
                  <span className="text-red-500 font-black text-lg">↓</span>
                  <div>
                    <p className="text-sm font-bold">Bear regime warning</p>
                    <p className="text-xs text-muted-foreground">Weekly close below <strong className="text-foreground">${formatPriceCompact(regime.ema50)}</strong></p>
                  </div>
                </div>
                <p className="text-xs text-muted-foreground">If BTC closes below ${formatPriceCompact(regime.ema50)} on a weekly candle, shift to shorts and reduce spot exposure.</p>
              </div>
            )}
          </div>

          {/* Best setups right now */}
          {alignedSetups.length > 0 && (
            <div className="bg-muted/30 rounded-xl p-4 space-y-3">
              <h3 className="text-xs font-black uppercase tracking-widest text-muted-foreground">
                Best {isBear ? "Short" : "Long"} Setups Right Now
              </h3>
              <div className="space-y-2">
                {alignedSetups.map((s: BestSetupItem) => (
                  <div key={s.symbol} className="flex items-center justify-between p-2.5 rounded-lg bg-background border border-border/50">
                    <div>
                      <span className="font-black text-sm">{s.symbol.replace("/USDT", "")}</span>
                      <span className={cn("ml-2 text-[9px] font-bold px-1.5 py-0.5 rounded",
                        isBear ? "bg-red-500/15 text-red-500" : "bg-green-500/15 text-green-500"
                      )}>{s.direction}</span>
                    </div>
                    <div className="text-right">
                      <p className="text-xs font-mono font-medium">${formatPriceCompact(s.entry)}</p>
                      <p className="text-[10px] text-muted-foreground">conviction {s.conviction}%</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Counter-trend setups (warning) */}
          {counterSetups.length > 0 && (
            <div className="bg-yellow-500/5 rounded-xl p-4 space-y-3 border border-yellow-500/15">
              <h3 className="text-xs font-black uppercase tracking-widest text-yellow-600 dark:text-yellow-400">
                Counter-Trend (Higher Risk)
              </h3>
              <div className="space-y-2">
                {counterSetups.map((s: BestSetupItem) => (
                  <div key={s.symbol} className="flex items-center justify-between p-2.5 rounded-lg bg-background border border-border/50 opacity-70">
                    <div>
                      <span className="font-black text-sm">{s.symbol.replace("/USDT", "")}</span>
                      <span className="ml-2 text-[9px] font-bold px-1.5 py-0.5 rounded bg-yellow-500/15 text-yellow-600 dark:text-yellow-400">{s.direction}</span>
                    </div>
                    <div className="text-right">
                      <p className="text-xs font-mono font-medium">${formatPriceCompact(s.entry)}</p>
                      <p className="text-[10px] text-muted-foreground">conviction {s.conviction}%</p>
                    </div>
                  </div>
                ))}
              </div>
              <p className="text-[10px] text-muted-foreground">These go against the regime. Only take if you have a strong reason.</p>
            </div>
          )}

          {/* How to Execute — Spot vs Limit */}
          <div className="bg-muted/30 rounded-xl p-4 space-y-3">
            <h3 className="text-xs font-black uppercase tracking-widest text-muted-foreground">How To Execute</h3>
            {isBear ? (
              <div className="space-y-3">
                <div className="p-3 rounded-lg bg-red-500/5 border border-red-500/15">
                  <p className="text-xs font-black text-red-500 uppercase tracking-wider mb-1.5">Spot Buying</p>
                  <p className="text-sm">Don&apos;t. BTC is below EMA50 — spot longs are fighting the trend. Wait for bull cross.</p>
                </div>
                <div className="p-3 rounded-lg bg-background border border-border/50">
                  <p className="text-xs font-black text-foreground uppercase tracking-wider mb-1.5">Limit Shorts</p>
                  <p className="text-sm">Use the setups above. Enter on limit near resistance / rejection zones. Set SL above recent highs.</p>
                  <p className="text-xs text-muted-foreground mt-1">Futures only. Use 3-5x leverage max.</p>
                </div>
                <div className="p-3 rounded-lg bg-background border border-border/50">
                  <p className="text-xs font-black text-foreground uppercase tracking-wider mb-1.5">Spot Sell / Exit</p>
                  <p className="text-sm">If holding spot, consider reducing exposure. Move to stablecoins until bull cross.</p>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="p-3 rounded-lg bg-green-500/5 border border-green-500/15">
                  <p className="text-xs font-black text-green-500 uppercase tracking-wider mb-1.5">Spot Buying</p>
                  <p className="text-sm">Yes. HODL BTC. Buy dips on alts with long setups. Market is trending up.</p>
                </div>
                <div className="p-3 rounded-lg bg-background border border-border/50">
                  <p className="text-xs font-black text-foreground uppercase tracking-wider mb-1.5">Limit Longs</p>
                  <p className="text-sm">Use the setups above. Enter on limit near support / pullback zones. Set SL below recent lows.</p>
                  <p className="text-xs text-muted-foreground mt-1">Spot or futures. Higher conviction than shorts.</p>
                </div>
                <div className="p-3 rounded-lg bg-yellow-500/5 border border-yellow-500/15">
                  <p className="text-xs font-black text-yellow-600 dark:text-yellow-400 uppercase tracking-wider mb-1.5">Limit Shorts</p>
                  <p className="text-sm">Counter-trend. Only for experienced traders. Use tight stops. Prefer the setups above on specific coins.</p>
                </div>
              </div>
            )}

          </div>

          {/* BTC Position */}
          <div className="bg-muted/30 rounded-xl p-4 space-y-3">
            <h3 className="text-xs font-black uppercase tracking-widest text-muted-foreground">BTC Position</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-[10px] text-muted-foreground uppercase font-bold">BTC Price</p>
                <p className="text-xl font-medium font-mono">${formatPriceCompact(regime.btc_price)}</p>
              </div>
              <div>
                <p className="text-[10px] text-muted-foreground uppercase font-bold">EMA50 (Weekly)</p>
                <p className="text-xl font-medium font-mono">${formatPriceCompact(regime.ema50)}</p>
              </div>
            </div>
            <div className="space-y-1">
              <div className="flex justify-between text-[10px] font-bold text-muted-foreground">
                <span>Distance</span>
                <span className={cn(regime.distance_pct > 0 ? "text-green-500" : "text-red-500")}>
                  {regime.distance_pct > 0 ? "+" : ""}{regime.distance_pct}%
                </span>
              </div>
              <div className="h-2 bg-muted rounded-full relative overflow-hidden">
                <div className="absolute inset-y-0 left-1/2 w-px bg-border" />
                <div
                  className={cn(
                    "absolute inset-y-0 rounded-full",
                    regime.distance_pct > 0 ? "bg-green-500/40 left-1/2" : "bg-red-500/40 right-1/2"
                  )}
                  style={{ width: `${Math.min(50, Math.abs(regime.distance_pct) / 2)}%` }}
                />
              </div>
              <div className="flex justify-between text-[9px] text-muted-foreground">
                <span>Bear zone</span>
                <span>EMA50</span>
                <span>Bull zone</span>
              </div>
            </div>
          </div>

          {/* Market Context */}
          <div className="bg-muted/30 rounded-xl p-4">
            <h3 className="text-xs font-black uppercase tracking-widest text-muted-foreground mb-3">Market Context</h3>
            <div className="grid grid-cols-3 gap-3">
              {rsi !== undefined && (
                <div className="text-center">
                  <p className="text-[10px] text-muted-foreground uppercase font-bold">RSI</p>
                  <p className={cn("text-lg font-medium font-mono",
                    rsi > 70 ? "text-red-500" : rsi < 30 ? "text-green-500" : "text-foreground"
                  )}>{rsi.toFixed(0)}</p>
                  <p className="text-[9px] text-muted-foreground">{rsi > 70 ? "Overbought" : rsi < 30 ? "Oversold" : "Neutral"}</p>
                </div>
              )}
              {cap !== undefined && (
                <div className="text-center">
                  <p className="text-[10px] text-muted-foreground uppercase font-bold">MCap</p>
                  <p className="text-lg font-medium font-mono">{formatVolume(cap)}</p>
                  <p className="text-[9px] text-muted-foreground">{indicators?.total_market_cap?.regime ?? "—"}</p>
                </div>
              )}
              {dom !== undefined && (
                <div className="text-center">
                  <p className="text-[10px] text-muted-foreground uppercase font-bold">BTC Dom</p>
                  <p className="text-lg font-medium font-mono">{dom.toFixed(1)}%</p>
                  <p className="text-[9px] text-muted-foreground">{dom > 55 ? "Heavy" : dom < 45 ? "Alt Season" : "Balanced"}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export function DashboardStatusBar() {
  const queryClient = useQueryClient();
  const { data: indicators, refetch: refetchIndicators } = useMarketIndicators();
  const { data: regime, isLoading: loading, refetch: refetchRegime } = useRegime("4h");

  const [modalOpen, setModalOpen] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = async () => {
    setRefreshing(true);
    await Promise.all([
      refetchRegime(),
      refetchIndicators(),
      queryClient.invalidateQueries({ queryKey: ["analytics", "best-setups"] }),
      queryClient.invalidateQueries({ queryKey: ["tickers"] }),
    ]);
    setRefreshing(false);
  };

  const regimeLabel = regime?.regime ?? "—";
  const isBull = regimeLabel === "BULL";
  const isBear = regimeLabel === "BEAR";
  const stateColor = isBull ? "text-green-600 dark:text-green-400" : isBear ? "text-red-600 dark:text-red-400" : "text-muted-foreground";
  const bgColor = isBull ? "bg-green-500/5 border-green-500/20" : isBear ? "bg-red-500/5 border-red-500/20" : "bg-secondary/30 border-border/50";

  const rsi = indicators?.average_rsi?.value;
  const rsiColor = rsi !== undefined ? (rsi > 70 ? "text-red-600 dark:text-red-400" : rsi < 30 ? "text-green-600 dark:text-green-400" : "text-muted-foreground") : "text-muted-foreground";
  const rsiStatus = rsi !== undefined ? (rsi > 70 ? "OB" : rsi < 30 ? "OS" : "") : null;

  const cap = indicators?.total_market_cap?.value;
  const capColor = indicators?.total_market_cap?.regime === "BULLISH" ? "text-green-600 dark:text-green-400" : indicators?.total_market_cap?.regime === "BEARISH" ? "text-red-600 dark:text-red-400" : "text-muted-foreground";

  const dom = indicators?.btc_dominance?.value;
  const domColor = dom !== undefined ? (dom > 55 ? "text-yellow-600 dark:text-yellow-400" : dom < 45 ? "text-purple-600 dark:text-purple-400" : "text-muted-foreground") : "text-muted-foreground";
  const domStatus = dom !== undefined ? (dom > 55 ? "Heavy" : dom < 45 ? "Alt Season" : "") : null;

  if (loading && !regime) {
    return <div className="h-10 rounded-xl bg-secondary/30 border border-border/50 animate-pulse" />;
  }

  return (
    <>
      <div
        className={cn("flex items-center gap-3 px-4 h-10 rounded-xl border text-xs font-bold overflow-x-auto scrollbar-none cursor-pointer hover:brightness-110 transition-all", bgColor)}
        onClick={() => setModalOpen(true)}
      >
        {/* Regime badge */}
        <div className="flex items-center gap-1.5 shrink-0">
          {isBull ? <TrendingUp size={11} className={stateColor} /> : isBear ? <TrendingDown size={11} className={stateColor} /> : null}
          <span className={cn("font-black uppercase tracking-wide", stateColor)}>{regimeLabel}</span>
        </div>

        {regime && (
          <>
            <Divider />
            <span className="shrink-0 text-muted-foreground">
              EMA50 <span className="font-mono">${regime.ema50?.toLocaleString("en-US", { maximumFractionDigits: 0 })}</span>
              <span className={cn("ml-1 text-[9px]", regime.distance_pct > 0 ? "text-green-500" : "text-red-500")}>
                {regime.distance_pct > 0 ? "+" : ""}{regime.distance_pct}%
              </span>
            </span>

            {regime.approaching_cross && (
              <>
                <Divider />
                <span className="shrink-0 text-yellow-600 dark:text-yellow-400 text-[10px]">
                  ⚡ {regime.anticipation}
                </span>
              </>
            )}
          </>
        )}

        {rsi !== undefined && (
          <>
            <Divider />
            <span className="shrink-0 text-muted-foreground">
              RSI <span className={cn("font-black", rsiColor)}>{rsi.toFixed(1)}</span>
              {rsiStatus && <span className={cn("ml-1 text-[9px]", rsiColor)}>{rsiStatus}</span>}
            </span>
          </>
        )}

        {cap !== undefined && (
          <>
            <Divider />
            <span className="shrink-0 text-muted-foreground">
              MCap <span className={cn("font-black", capColor)}>{formatVolume(cap)}</span>
            </span>
          </>
        )}

        {dom !== undefined && (
          <>
            <Divider />
            <span className="shrink-0 text-muted-foreground">
              BTC Dom <span className={cn("font-black", domColor)}>{dom.toFixed(1)}%</span>
              {domStatus && <span className={cn("ml-1 text-[9px]", domColor)}>{domStatus}</span>}
            </span>
          </>
        )}

        <button
          onClick={(e) => { e.stopPropagation(); handleRefresh(); }}
          disabled={refreshing}
          className="ml-auto shrink-0 text-muted-foreground hover:text-foreground transition-colors disabled:opacity-40"
          title="Refresh all"
        >
          <RefreshCcw size={12} className={cn(refreshing && "animate-spin")} />
        </button>
      </div>

      {modalOpen && <RegimeModal regime={regime ?? null} indicators={indicators} onClose={() => setModalOpen(false)} />}
    </>
  );
}
