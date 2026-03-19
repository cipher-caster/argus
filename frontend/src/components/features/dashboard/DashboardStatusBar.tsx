"use client";

import { useMarketIndicators } from "@/hooks/useMarketIndicators";
import { formatVolume } from "@/lib/formatters";
import { cn } from "@/lib/utils";
import { RefreshCcw, TrendingDown, TrendingUp, X } from "lucide-react";
import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface RegimeData {
  regime: string;
  btc_price: number;
  ema50: number;
  distance_pct: number;
  ema50_slope: string;
  approaching_cross: boolean;
  anticipation: string;
}

function Divider() {
  return <div className="h-4 w-px bg-border/50 shrink-0" />;
}

function RegimeModal({ regime, indicators, onClose }: { regime: RegimeData | null; indicators: any; onClose: () => void }) {
  if (!regime) return null;

  const isBull = regime.regime === "BULL";
  const isBear = regime.regime === "BEAR";

  const rsi = indicators?.average_rsi?.value;
  const cap = indicators?.total_market_cap?.value;
  const dom = indicators?.btc_dominance?.value;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div
        className="bg-background border border-border rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className={cn(
          "flex items-center justify-between px-6 py-4 border-b",
          isBull ? "bg-green-500/10 border-green-500/20" : "bg-red-500/10 border-red-500/20"
        )}>
          <div className="flex items-center gap-3">
            {isBull ? <TrendingUp size={20} className="text-green-500" /> : <TrendingDown size={20} className="text-red-500" />}
            <div>
              <h2 className="text-lg font-black uppercase tracking-wider">{regime.regime} Market</h2>
              <p className="text-xs text-muted-foreground">Based on BTC Weekly EMA50</p>
            </div>
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground transition-colors">
            <X size={18} />
          </button>
        </div>

        <div className="p-6 space-y-5">
          {/* What this means */}
          <div className="space-y-2">
            <h3 className="text-xs font-black uppercase tracking-widest text-muted-foreground">What this means</h3>
            <p className="text-sm leading-relaxed">
              {isBull
                ? "BTC is trading above its 50-week moving average. Historically, this means the market is in an uptrend. Best approach: hold BTC or look for long setups on altcoins."
                : "BTC is trading below its 50-week moving average. The market is in a downtrend. Best approach: short setups or stay in stablecoins. Don't fight the trend."
              }
            </p>
          </div>

          {/* BTC vs EMA50 */}
          <div className="bg-muted/30 rounded-xl p-4 space-y-3">
            <h3 className="text-xs font-black uppercase tracking-widest text-muted-foreground">BTC Position</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-[10px] text-muted-foreground uppercase font-bold">BTC Price</p>
                <p className="text-xl font-black font-mono">${regime.btc_price?.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-[10px] text-muted-foreground uppercase font-bold">EMA50 (Weekly)</p>
                <p className="text-xl font-black font-mono">${regime.ema50?.toLocaleString()}</p>
              </div>
            </div>

            {/* Visual bar */}
            <div className="space-y-1">
              <div className="flex justify-between text-[10px] font-bold text-muted-foreground">
                <span>Distance</span>
                <span className={cn(regime.distance_pct > 0 ? "text-green-500" : "text-red-500")}>
                  {regime.distance_pct > 0 ? "+" : ""}{regime.distance_pct}%
                </span>
              </div>
              <div className="h-2 bg-muted rounded-full relative overflow-hidden">
                <div className={cn("absolute inset-y-0 left-1/2 w-px bg-border")} />
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

            <div className="flex items-center gap-2 text-xs">
              <span className="text-muted-foreground">EMA50 trend:</span>
              <span className={cn("font-bold", regime.ema50_slope === "rising" ? "text-green-500" : "text-red-500")}>
                {regime.ema50_slope === "rising" ? "↑ Rising" : "↓ Falling"}
              </span>
            </div>
          </div>

          {/* Anticipation */}
          <div className={cn(
            "rounded-xl p-4 space-y-2",
            regime.approaching_cross ? "bg-yellow-500/10 border border-yellow-500/20" : "bg-muted/30"
          )}>
            <h3 className="text-xs font-black uppercase tracking-widest text-muted-foreground">
              {regime.approaching_cross ? "⚡ Watch Point" : "Next Level"}
            </h3>
            <p className="text-sm font-medium">{regime.anticipation}</p>
          </div>

          {/* Market Indicators */}
          <div className="bg-muted/30 rounded-xl p-4 space-y-3">
            <h3 className="text-xs font-black uppercase tracking-widest text-muted-foreground">Market Context</h3>
            <div className="grid grid-cols-3 gap-3">
              {rsi !== undefined && (
                <div className="text-center">
                  <p className="text-[10px] text-muted-foreground uppercase font-bold">RSI</p>
                  <p className={cn("text-lg font-black font-mono",
                    rsi > 70 ? "text-red-500" : rsi < 30 ? "text-green-500" : "text-foreground"
                  )}>{rsi.toFixed(0)}</p>
                  <p className="text-[9px] text-muted-foreground">{rsi > 70 ? "Overbought" : rsi < 30 ? "Oversold" : "Neutral"}</p>
                </div>
              )}
              {cap !== undefined && (
                <div className="text-center">
                  <p className="text-[10px] text-muted-foreground uppercase font-bold">MCap</p>
                  <p className="text-lg font-black font-mono">{formatVolume(cap)}</p>
                  <p className="text-[9px] text-muted-foreground">{indicators?.total_market_cap?.regime ?? "—"}</p>
                </div>
              )}
              {dom !== undefined && (
                <div className="text-center">
                  <p className="text-[10px] text-muted-foreground uppercase font-bold">BTC Dom</p>
                  <p className="text-lg font-black font-mono">{dom.toFixed(1)}%</p>
                  <p className="text-[9px] text-muted-foreground">{dom > 55 ? "Heavy" : dom < 45 ? "Alt Season" : "Balanced"}</p>
                </div>
              )}
            </div>
          </div>

          {/* Action summary */}
          <div className="border-t border-border pt-4">
            <h3 className="text-xs font-black uppercase tracking-widest text-muted-foreground mb-2">Action Summary</h3>
            <ul className="space-y-1.5 text-sm">
              {isBear ? (
                <>
                  <li className="flex items-start gap-2">
                    <span className="text-red-500 mt-0.5">•</span>
                    <span>Prioritize <strong>short</strong> setups on Titan signals</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-red-500 mt-0.5">•</span>
                    <span>Avoid holding spot longs — trend is against you</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-muted-foreground mt-0.5">•</span>
                    <span className="text-muted-foreground">Watch for bull cross at weekly close above <strong>${regime.ema50?.toLocaleString()}</strong></span>
                  </li>
                </>
              ) : (
                <>
                  <li className="flex items-start gap-2">
                    <span className="text-green-500 mt-0.5">•</span>
                    <span><strong>HODL</strong> BTC or look for long setups on alts</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-500 mt-0.5">•</span>
                    <span>Shorts are counter-trend — higher risk</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-muted-foreground mt-0.5">•</span>
                    <span className="text-muted-foreground">Watch for bear cross if BTC closes below <strong>${regime.ema50?.toLocaleString()}</strong></span>
                  </li>
                </>
              )}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export function DashboardStatusBar() {
  const { data: indicators } = useMarketIndicators();
  const [regime, setRegime] = useState<RegimeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);

  const fetchRegime = async () => {
    try {
      const res = await fetch(`${API_URL}/api/strategy/regime`);
      if (res.ok) setRegime(await res.json());
    } catch {} finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchRegime(); }, []);

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
          onClick={(e) => { e.stopPropagation(); fetchRegime(); }}
          className="ml-auto shrink-0 text-muted-foreground hover:text-foreground transition-colors"
          title="Refresh"
        >
          <RefreshCcw size={12} />
        </button>
      </div>

      {modalOpen && <RegimeModal regime={regime} indicators={indicators} onClose={() => setModalOpen(false)} />}
    </>
  );
}
