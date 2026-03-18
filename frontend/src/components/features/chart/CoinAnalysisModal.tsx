"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { X, Target, TrendingUp, TrendingDown, ShieldAlert, Zap, AlertTriangle, BarChart2, History, Activity } from "lucide-react";
import { cn } from "@/lib/utils";
import { OracleStrategyResponse, TitanStrategyResponse, SignalLogItem } from "@/lib/api";
import { useStrategyTitan } from "@/hooks/useStrategyTitan";
import { useBacktestStats, useSignalLog } from "@/hooks/useAnalyticsData";
import { Badge } from "@/components/ui/badge";

interface CoinAnalysisModalProps {
  isOpen: boolean;
  onClose: () => void;
  symbol: string;
  timeframe: string;
  oracle: OracleStrategyResponse;
}

// ─── Derivation helpers ─────────────────────────────────────────────────────

type Stance = "BUY" | "BUY_LIMIT" | "WAIT" | "AVOID";

interface SpotSetup {
  stance: Stance;
  reason: string;
  entry: number | undefined;
  tp1: number | undefined;
  tp2: number | undefined;
  maxTarget: number | undefined;
  sl: number | undefined;
  entryNote: string;
  rr1: number | undefined;
  rr2: number | undefined;
  rrMax: number | undefined;
}

function deriveMaxTarget(entry: number, tp2: number, oracle: OracleStrategyResponse): number {
  const hist = oracle.historical_signals.slice(-50);
  const swingHigh = hist.length > 0 ? Math.max(...hist.map((s) => s.price)) : undefined;
  // Use swing high if meaningfully above TP2, otherwise extend TP2 by the TP1→TP2 range
  if (swingHigh && swingHigh > tp2 * 1.005) return swingHigh;
  return entry + 2 * (tp2 - entry);
}

function deriveSpotSetup(
  oracle: OracleStrategyResponse,
  titan: TitanStrategyResponse,
  price: number
): SpotSetup {
  const oracleBullish = oracle.signal === "STRONG_BUY" || oracle.signal === "BUY";
  const oracleBearish = oracle.signal === "STRONG_SELL" || oracle.signal === "SELL";
  const titanBullish = titan.signal === "BUY" || titan.signal === "BUY_LIMIT";

  if (oracleBullish && titanBullish) {
    const useLimit = titan.signal === "BUY_LIMIT" && titan.targets.entry < price;
    const entry = useLimit ? titan.targets.entry : price;
    const tp1 = oracle.targets.tp1 > 0 ? oracle.targets.tp1 : undefined;
    const tp2 = oracle.targets.tp2 > 0 ? oracle.targets.tp2 : titan.targets.tp;
    const sl = titan.targets.sl;
    const maxTarget = tp2 ? deriveMaxTarget(entry, tp2, oracle) : undefined;
    const rr1 = tp1 ? (tp1 - entry) / (entry - sl) : undefined;
    const rr2 = tp2 ? (tp2 - entry) / (entry - sl) : undefined;
    const rrMax = maxTarget ? (maxTarget - entry) / (entry - sl) : undefined;
    
    let reason = useLimit
      ? `Oracle ${oracle.signal.replace("_", " ")} + Titan BULLISH. Wait for pullback to EMA20.`
      : "Oracle and Titan both bullish — confirmed entry.";
    
    if (titan.confidence >= 95) {
      reason = `[INSTITUTIONAL EDGE] ${reason}`;
    }

    return {
      stance: useLimit ? "BUY_LIMIT" : "BUY",
      reason,
      entry, tp1, tp2, maxTarget, sl, rr1, rr2, rrMax,
      entryNote: useLimit
        ? `Limit ~${(((price - entry) / price) * 100).toFixed(1)}% below current`
        : "Market order",
    };
  }

  if (oracleBearish) {
    return {
      stance: "AVOID",
      reason: `Oracle is ${oracle.signal.replace("_", " ")} — no spot buy.`,
      entry: undefined, tp1: undefined, tp2: undefined, maxTarget: undefined, sl: undefined,
      rr1: undefined, rr2: undefined, rrMax: undefined,
      entryNote: `Watch for bounce at SuperTrend $${titan.indicators.supertrend.toFixed(2)}`,
    };
  }

  // NEUTRAL or disagreement
  const ema20 = titan.indicators.ema20;
  const waitLevel = ema20 > price ? ema20 : titan.targets.entry;
  const tp1 = oracle.targets.tp1 > 0 ? oracle.targets.tp1 : titan.targets.tp;
  const tp2raw = oracle.targets.tp2 > 0 ? oracle.targets.tp2 : undefined;
  const sl = titan.targets.sl;
  const maxTarget = tp2raw ? deriveMaxTarget(waitLevel, tp2raw, oracle) : undefined;
  const rr1 = sl > 0 && waitLevel > sl ? (tp1 - waitLevel) / (waitLevel - sl) : undefined;
  const rrMax = maxTarget && sl > 0 ? (maxTarget - waitLevel) / (waitLevel - sl) : undefined;
  return {
    stance: "WAIT",
    reason: `Oracle ${oracle.signal} — wait for 1H close above $${waitLevel.toFixed(2)} for confirmation.`,
    entry: waitLevel,
    tp1, tp2: tp2raw, maxTarget,
    sl, rr1, rr2: undefined, rrMax,
    entryNote: `On confirmed 1H close above $${waitLevel.toFixed(2)}`,
  };
}

interface KeyLevel { label: string; price: number; note: string }

function deriveKeyLevels(
  oracle: OracleStrategyResponse,
  titan: TitanStrategyResponse,
  price: number
) {
  const hist = oracle.historical_signals.slice(-50);
  const swingHigh = hist.length > 0 ? Math.max(...hist.map((s) => s.price)) : undefined;
  const swingLow = hist.length > 0 ? Math.min(...hist.map((s) => s.price)) : undefined;

  const resistances: KeyLevel[] = [
    titan.indicators.ema20 > price
      ? { label: "EMA20 (4H)", price: titan.indicators.ema20, note: "Immediate resistance — break = bullish" }
      : null,
    swingHigh && swingHigh > price
      ? { label: "Swing High", price: swingHigh, note: "Recent high cluster — key resistance" }
      : null,
  ].filter(Boolean).sort((a, b) => a!.price - b!.price) as KeyLevel[];

  const supports: KeyLevel[] = [
    titan.indicators.ema20 <= price
      ? { label: "EMA20 (4H)", price: titan.indicators.ema20, note: "Ideal limit entry zone" }
      : null,
    { label: "EMA50 (4H)", price: titan.indicators.ema50, note: "First cushion" },
    { label: "SuperTrend", price: titan.indicators.supertrend, note: "Trend floor — 4H close below = bearish flip" },
    swingLow && swingLow < price
      ? { label: "Swing Low", price: swingLow, note: "Deep support / capitulation zone" }
      : null,
  ].filter(Boolean).sort((a, b) => b!.price - a!.price) as KeyLevel[];

  return { resistances, supports };
}

function deriveSummary(
  oracle: OracleStrategyResponse,
  titan: TitanStrategyResponse,
  price: number,
  setup: SpotSetup,
  levels: ReturnType<typeof deriveKeyLevels>
): string {
  const base = oracle.symbol.replace("/USDT", "");
  const oracleStr = oracle.signal.replace(/_/g, " ");
  const situation = `${base} is trading at $${price.toFixed(2)} with Oracle ${oracleStr} (${oracle.earnest.score}/5 voters) and Titan ${titan.trend} trend (${titan.confidence}% confidence).`;

  const bullLevel = levels.resistances[0]?.price ?? setup.tp1;
  const bullTrigger =
    setup.stance === "BUY" || setup.stance === "BUY_LIMIT"
      ? `Entry plan: ${setup.entryNote} — targets $${setup.tp1?.toFixed(2) ?? "—"} then $${setup.tp2?.toFixed(2) ?? "—"}.`
      : `Bull trigger: 1H close above $${bullLevel?.toFixed(2) ?? "resistance"} to confirm continuation.`;

  const supertrend = titan.indicators.supertrend;
  const bearTrigger = `Bear trigger: 4H close below SuperTrend at $${supertrend.toFixed(2)} flips Titan bearish — avoid longs below that level.`;

  const action =
    setup.stance === "AVOID"
      ? `Avoid spot buys now. ${setup.entryNote}.`
      : setup.stance === "WAIT"
      ? `Set an alert at $${setup.entry?.toFixed(2)} and wait for confirmation before entering.`
      : `Place ${setup.stance === "BUY_LIMIT" ? "limit" : "market"} order at $${setup.entry?.toFixed(2)}, cut loss at $${setup.sl?.toFixed(2)}.`;

  return [situation, bullTrigger, bearTrigger, action].join(" ");
}

// ─── Sub-components ──────────────────────────────────────────────────────────

function SectionTitle({ icon, children }: { icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2 mb-3">
      <span className="text-muted-foreground">{icon}</span>
      <span className="text-[11px] font-bold uppercase tracking-widest text-muted-foreground">{children}</span>
    </div>
  );
}

function StanceColors(stance: Stance) {
  if (stance === "BUY" || stance === "BUY_LIMIT")
    return "text-emerald-700 dark:text-emerald-400 bg-emerald-500/10 border-emerald-500/30";
  if (stance === "AVOID")
    return "text-rose-700 dark:text-rose-400 bg-rose-500/10 border-rose-500/30";
  return "text-amber-700 dark:text-amber-400 bg-amber-500/10 border-amber-500/30";
}

function SignalBadgeClass(signal: string) {
  if (signal.includes("BUY"))
    return "text-emerald-700 dark:text-emerald-400 bg-emerald-500/10 border-emerald-500/20";
  if (signal.includes("SELL"))
    return "text-rose-700 dark:text-rose-400 bg-rose-500/10 border-rose-500/20";
  return "text-slate-600 dark:text-slate-400 bg-slate-400/10 border-slate-400/20";
}

function fmt(n: number | undefined, digits = 2): string {
  if (n === undefined) return "—";
  return n.toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

function VoterDot({ score }: { score: number }) {
  return (
    <span
      className={cn(
        "inline-block w-4 h-4 rounded-full text-[9px] font-black flex items-center justify-center",
        score > 0 ? "bg-emerald-500/20 text-emerald-600 dark:text-emerald-400" :
        score < 0 ? "bg-rose-500/20 text-rose-600 dark:text-rose-400" :
        "bg-muted text-muted-foreground"
      )}
    >
      {score > 0 ? `+${score}` : score}
    </span>
  );
}

// ─── Signal Track Record ─────────────────────────────────────────────────────

function formatSignalDate(ms: number) {
  const d = new Date(ms);
  const mon = d.toLocaleString("en-US", { month: "short" });
  return `${mon} ${d.getDate()}, ${d.getFullYear()} ${d.getHours().toString().padStart(2, "0")}:${d.getMinutes().toString().padStart(2, "0")}`;
}

function formatSignalPrice(p: number) {
  if (p >= 1000) return p.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  if (p >= 1) return p.toFixed(4);
  return p.toFixed(6);
}

const OUTCOME_STYLE = {
  WIN: "text-emerald-500 bg-emerald-500/10",
  LOSS: "text-red-500 bg-red-500/10",
  REVIEW: "text-amber-500 bg-amber-500/10",
  OPEN: "text-sky-500 bg-sky-500/10",
} as const;

function SignalTrackRecord({ symbol, currentPrice }: { symbol: string; currentPrice: number }) {
  const symbolKey = symbol.replace("/", "");
  const { data: backtestData } = useBacktestStats();
  const { data: signalData, isLoading } = useSignalLog(symbolKey, undefined, 50);

  const coinStats = backtestData?.coins?.find((c) => c.symbol === symbolKey);
  const signals = signalData?.data ?? [];
  const openSignals = signals.filter((s) => s.outcome === "OPEN");
  const closedSignals = signals.filter((s) => s.outcome !== "OPEN");

  if (!coinStats && !signals.length && !isLoading) return null;

  const wr = coinStats?.win_rate ?? 0;
  const isProfitable = coinStats && coinStats.profit_r > 0 && wr > 40;
  const isMarginal = coinStats && wr > 33 && !isProfitable;

  return (
    <div className="p-5 space-y-3">
      <SectionTitle icon={<Activity size={13} />}>Signal Track Record</SectionTitle>

      {/* Backtest Stats */}
      {coinStats && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
          {[
            {
              label: "Win Rate",
              value: `${wr}%`,
              cls: wr >= 45 ? "text-emerald-500" : wr >= 33 ? "text-amber-500" : "text-red-500",
            },
            {
              label: "Profit",
              value: `${coinStats.profit_r > 0 ? "+" : ""}${coinStats.profit_r}R`,
              cls: coinStats.profit_r > 0 ? "text-emerald-500" : coinStats.profit_r < 0 ? "text-red-500" : "text-muted-foreground",
            },
            { label: "Signals", value: `${coinStats.total}`, cls: "text-foreground" },
            { label: "Long WR", value: `${coinStats.long_wr ?? 0}%`, cls: "text-emerald-500" },
            { label: "Short WR", value: `${coinStats.short_wr ?? 0}%`, cls: "text-red-500" },
          ].map(({ label, value, cls }) => (
            <div key={label} className="p-2 rounded-lg bg-muted/30 border border-border/50 text-center">
              <div className={cn("text-sm font-black", cls)}>{value}</div>
              <div className="text-[8px] text-muted-foreground font-bold uppercase tracking-widest">{label}</div>
            </div>
          ))}
        </div>
      )}

      {coinStats && (
        <div className="flex items-center gap-2">
          <div className="h-2 rounded-full bg-secondary/60 flex-1 overflow-hidden">
            <div
              className={cn("h-full rounded-full",
                wr >= 45 ? "bg-emerald-500" : wr >= 33 ? "bg-amber-500" : "bg-red-500"
              )}
              style={{ width: `${wr}%` }}
            />
          </div>
          <span className={cn("text-[10px] font-black px-2 py-0.5 rounded-md",
            isProfitable ? "bg-emerald-500/10 text-emerald-500" :
            isMarginal ? "bg-amber-500/10 text-amber-500" : "bg-red-500/10 text-red-500"
          )}>
            {isProfitable ? "PROFITABLE" : isMarginal ? "MARGINAL" : "UNPROFITABLE"}
          </span>
        </div>
      )}

      {/* Open Signals */}
      {openSignals.length > 0 && (
        <div className="space-y-1.5">
          <div className="text-[10px] font-bold text-sky-500 uppercase tracking-wider">Active Signals</div>
          {openSignals.map((s) => {
            const isLong = s.direction === "LONG";
            const distToTp = isLong
              ? ((s.tp - currentPrice) / currentPrice * 100)
              : ((currentPrice - s.tp) / currentPrice * 100);
            const distToSl = isLong
              ? ((currentPrice - s.sl) / currentPrice * 100)
              : ((s.sl - currentPrice) / currentPrice * 100);
            return (
              <div key={s.id} className="flex items-center justify-between p-2.5 rounded-lg bg-sky-500/[0.05] border border-sky-500/20">
                <div className="flex items-center gap-2">
                  <span className={cn("text-[10px] font-black px-1.5 py-0.5 rounded",
                    isLong ? "bg-emerald-500/10 text-emerald-500" : "bg-red-500/10 text-red-500"
                  )}>{s.direction}</span>
                  <span className="text-[11px] font-mono text-muted-foreground">E: ${formatSignalPrice(s.entry)}</span>
                </div>
                <div className="flex items-center gap-2 text-[10px] font-bold">
                  <span className="text-emerald-500">TP {distToTp > 0 ? "+" : ""}{distToTp.toFixed(1)}%</span>
                  <span className="text-red-500">SL {distToSl > 0 ? "+" : ""}{distToSl.toFixed(1)}%</span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Signal History Table */}
      {closedSignals.length > 0 && (
        <div className="space-y-1.5">
          <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Recent Signals</div>
          <div className="overflow-x-auto rounded-lg border border-border/40">
            <table className="w-full">
              <thead>
                <tr className="bg-muted/30 text-[9px] font-black uppercase tracking-widest text-muted-foreground">
                  <th className="py-2 px-2.5 text-left">Date</th>
                  <th className="py-2 px-2.5 text-left">Dir</th>
                  <th className="py-2 px-2.5 text-left">Entry</th>
                  <th className="py-2 px-2.5 text-left">TP</th>
                  <th className="py-2 px-2.5 text-left">SL</th>
                  <th className="py-2 px-2.5 text-left">Result</th>
                  <th className="py-2 px-2.5 text-left">Exit</th>
                </tr>
              </thead>
              <tbody>
                {closedSignals.map((s) => {
                  const isLong = s.direction === "LONG";
                  const outcomeStyle = OUTCOME_STYLE[s.outcome] ?? OUTCOME_STYLE.OPEN;
                  return (
                    <tr key={s.id} className="border-b border-border/20 text-[11px] hover:bg-secondary/20">
                      <td className="py-2 px-2.5 text-muted-foreground whitespace-nowrap">{formatSignalDate(s.fired_at)}</td>
                      <td className="py-2 px-2.5">
                        <span className={cn("text-[9px] font-black px-1 py-0.5 rounded",
                          isLong ? "bg-emerald-500/10 text-emerald-500" : "bg-red-500/10 text-red-500"
                        )}>{s.direction}</span>
                      </td>
                      <td className="py-2 px-2.5 font-mono text-muted-foreground">${formatSignalPrice(s.entry)}</td>
                      <td className="py-2 px-2.5 font-mono text-emerald-600 dark:text-emerald-400">${formatSignalPrice(s.tp)}</td>
                      <td className="py-2 px-2.5 font-mono text-red-600 dark:text-red-400">${formatSignalPrice(s.sl)}</td>
                      <td className="py-2 px-2.5">
                        <span className={cn("text-[9px] font-black px-1.5 py-0.5 rounded-md", outcomeStyle)}>{s.outcome}</span>
                      </td>
                      <td className="py-2 px-2.5 font-mono text-muted-foreground">
                        {s.resolved_price ? `$${formatSignalPrice(s.resolved_price)}` : "—"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {isLoading && !signals.length && (
        <div className="text-center text-[11px] text-muted-foreground py-4">Loading signal history…</div>
      )}
    </div>
  );
}

// ─── Modal body ──────────────────────────────────────────────────────────────

function AnalysisBody({ oracle, titan, price }: {
  oracle: OracleStrategyResponse;
  titan: TitanStrategyResponse;
  price: number;
}) {
  const setup = deriveSpotSetup(oracle, titan, price);
  const levels = deriveKeyLevels(oracle, titan, price);
  const summary = deriveSummary(oracle, titan, price, setup, levels);
  const isBullOracle = oracle.bias === "BULLISH";
  const isBearOracle = oracle.bias === "BEARISH";
  const hasFVG = !!oracle.active_fvg_type;
  const hasMSS = !!titan.mss_type;
  const hasSweep = !!titan.sweep_type;

  return (
    <div className="divide-y divide-border">
      {/* ── Summary ─────────────────────────────────────────────────── */}
      <div className="p-5">
        <SectionTitle icon={<ShieldAlert size={13} />}>Summary</SectionTitle>
        <p className="text-[12px] leading-relaxed text-muted-foreground">{summary}</p>
      </div>

      {/* ── Institutional Confluence (SMC) ──────────────────────────── */}
      {(hasFVG || hasMSS || hasSweep) && (
        <div className="p-5 bg-amber-500/5 space-y-3">
          <SectionTitle icon={<Target size={13} className="text-amber-600" />}>Institutional Context (SMC)</SectionTitle>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
            {hasFVG && (
              <div className="p-2 rounded-lg bg-background border border-amber-500/20">
                <div className="text-[9px] font-bold uppercase text-amber-600 mb-1">Fair Value Gap</div>
                <div className="text-xs font-bold text-foreground capitalize">{oracle.active_fvg_type} Gap Active</div>
              </div>
            )}
            {hasMSS && (
              <div className="p-2 rounded-lg bg-background border border-amber-500/20">
                <div className="text-[9px] font-bold uppercase text-amber-600 mb-1">Market Structure</div>
                <div className="text-xs font-bold text-foreground capitalize">{titan.mss_type} Shift @ ${fmt(titan.mss_price || 0)}</div>
              </div>
            )}
            {hasSweep && (
              <div className="p-2 rounded-lg bg-background border border-amber-500/20">
                <div className="text-[9px] font-bold uppercase text-amber-600 mb-1">Liquidity Grab</div>
                <div className="text-xs font-bold text-foreground capitalize">{titan.sweep_type} Sweep Detected</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Oracle Signal ───────────────────────────────────────────── */}
      <div className="p-5 space-y-3">
        <SectionTitle icon={<Zap size={13} />}>Oracle Signal ({oracle.micro_tf} / {oracle.macro_tf})</SectionTitle>

        <div className="flex items-center gap-3 flex-wrap">
          <Badge className={cn("text-sm font-bold px-3 py-1 border", SignalBadgeClass(oracle.signal))}>
            {oracle.signal.replace(/_/g, " ")}
          </Badge>
          <span className={cn("text-sm font-bold",
            isBullOracle ? "text-emerald-600 dark:text-emerald-400" :
            isBearOracle ? "text-rose-600 dark:text-rose-400" :
            "text-muted-foreground"
          )}>
            {oracle.bias}
          </span>
          <span className="text-xs text-muted-foreground">· {oracle.state} · {oracle.volatility} vol</span>
        </div>

        {/* Earnest voters */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {Object.entries(oracle.earnest.voters).map(([voter, score]) => (
            <div key={voter} className="flex items-center justify-between p-2 rounded-lg bg-muted/30 border border-border/50">
              <span className="text-[11px] font-bold uppercase text-muted-foreground">{voter}</span>
              <VoterDot score={score} />
            </div>
          ))}
        </div>

        {/* Macro filter */}
        <div className="p-3 rounded-lg bg-muted/20 border border-border/50 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Macro Filter (1D)</span>
            <span className={cn("text-xs font-bold",
              oracle.macro.bias === "BULLISH" ? "text-emerald-600 dark:text-emerald-400" :
              oracle.macro.bias === "BEARISH" ? "text-rose-600 dark:text-rose-400" :
              "text-muted-foreground"
            )}>
              Score {oracle.macro.score} · {oracle.macro.bias}
            </span>
          </div>
          <div className="flex gap-3 flex-wrap">
            {Object.entries(oracle.macro.details).map(([key, val]) => (
              <div key={key} className="flex items-center gap-1">
                {val
                  ? <TrendingUp size={10} className="text-emerald-500" />
                  : <TrendingDown size={10} className="text-rose-500" />}
                <span className="text-[10px] text-muted-foreground uppercase font-bold">{key}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Advice */}
        <div className="flex gap-2 p-3 rounded-lg bg-amber-500/5 border border-amber-500/20">
          <ShieldAlert size={13} className="text-amber-500 shrink-0 mt-0.5" />
          <p className="text-[11px] italic leading-relaxed text-amber-900 dark:text-amber-200/80">{oracle.advice}</p>
        </div>

        {/* Oracle targets + backtest */}
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5 p-3 rounded-lg bg-muted/20 border border-border/50">
            <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5 mb-2">
              <Target size={10} /> Targets
            </div>
            {oracle.targets.tp1 > 0 && (
              <div className="flex justify-between text-xs">
                <span className="text-muted-foreground">TP1</span>
                <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400">${fmt(oracle.targets.tp1)}</span>
              </div>
            )}
            {oracle.targets.tp2 > 0 && (
              <div className="flex justify-between text-xs">
                <span className="text-muted-foreground">TP2</span>
                <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400">${fmt(oracle.targets.tp2)}</span>
              </div>
            )}
            <div className="flex justify-between text-xs">
              <span className="text-muted-foreground">SL</span>
              <span className="font-mono font-bold text-rose-600 dark:text-rose-400">${fmt(oracle.targets.sl)}</span>
            </div>
          </div>

          <div className="space-y-1.5 p-3 rounded-lg bg-muted/20 border border-border/50">
            <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5 mb-2">
              <BarChart2 size={10} /> Backtest
            </div>
            {oracle.performance.total_trades < 10 ? (
              <p className="text-[10px] text-muted-foreground/70 italic">Insufficient data (&lt;10 trades)</p>
            ) : (
              <>
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">Win Rate</span>
                  <span className={cn("font-mono font-bold", oracle.performance.win_rate >= 33.3 ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400")}>
                    {oracle.performance.win_rate}%
                  </span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">Net PnL</span>
                  <span className={cn("font-mono font-bold", oracle.performance.net_profit >= 0 ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400")}>
                    {oracle.performance.net_profit > 0 ? "+" : ""}{oracle.performance.net_profit}%
                  </span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">Trades</span>
                  <span className="font-mono font-bold text-foreground">{oracle.performance.total_trades}</span>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* ── Titan Signal ────────────────────────────────────────────── */}
      <div className="p-5 space-y-3">
        <SectionTitle icon={<TrendingUp size={13} />}>Titan Signal ({titan.timeframe})</SectionTitle>

        <div className="flex items-center gap-3 flex-wrap">
          <Badge className={cn("text-sm font-bold px-3 py-1 border", SignalBadgeClass(titan.signal))}>
            {titan.signal.replace(/_/g, " ")}
          </Badge>
          <span className={cn("text-sm font-bold",
            titan.trend === "BULLISH" ? "text-emerald-600 dark:text-emerald-400" :
            titan.trend === "BEARISH" ? "text-rose-600 dark:text-rose-400" :
            "text-muted-foreground"
          )}>
            {titan.trend}
          </span>
          <span className="text-xs text-muted-foreground">· {titan.confidence}% confidence</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {[
            { label: "RSI", value: titan.indicators.rsi?.toFixed(1) ?? "—" },
            { label: "MACD", value: titan.indicators.macd?.toFixed(3) ?? "—" },
            { label: "SuperTrend", value: `$${fmt(titan.indicators.supertrend)}` },
            { label: "EMA20", value: `$${fmt(titan.indicators.ema20)}` },
            { label: "EMA50", value: `$${fmt(titan.indicators.ema50)}` },
            { label: "ATR", value: titan.volatility.atr.toFixed(3) },
          ].map(({ label, value }) => (
            <div key={label} className="flex flex-col p-2 rounded-lg bg-muted/30 border border-border/50">
              <span className="text-[9px] font-bold uppercase text-muted-foreground mb-0.5">{label}</span>
              <span className="text-xs font-mono font-bold text-foreground">{value}</span>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-3 gap-2">
          {[
            { label: "Entry", value: `$${fmt(titan.targets.entry)}`, color: "text-foreground" },
            { label: "Take Profit", value: `$${fmt(titan.targets.tp)}`, color: "text-emerald-600 dark:text-emerald-400" },
            { label: "Stop Loss", value: `$${fmt(titan.targets.sl)}`, color: "text-rose-600 dark:text-rose-400" },
          ].map(({ label, value, color }) => (
            <div key={label} className="flex flex-col items-center p-2.5 rounded-lg bg-muted/30 border border-border/50 text-center">
              <span className="text-[9px] font-bold uppercase text-muted-foreground mb-0.5">{label}</span>
              <span className={cn("text-xs font-mono font-bold", color)}>{value}</span>
            </div>
          ))}
        </div>

        <div className="text-[10px] text-muted-foreground">
          Momentum: <span className="font-bold text-foreground">{titan.momentum.status}</span>
          {titan.momentum.is_overbought && " · ⚠ Overbought"}
          {titan.momentum.is_oversold && " · ⚠ Oversold"}
          {titan.momentum.macd_crossed !== "NONE" && ` · MACD crossed ${titan.momentum.macd_crossed}`}
          {" · "}Sizing: <span className="font-bold text-foreground">{titan.sizing}</span>
        </div>
      </div>

      {/* ── Spot Setup ──────────────────────────────────────────────── */}
      <div className="p-5 space-y-3">
        <SectionTitle icon={<Target size={13} />}>Spot Setup</SectionTitle>

        <div className={cn("inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border text-sm font-bold", StanceColors(setup.stance))}>
          {setup.stance.replace("_", " ")}
        </div>
        <p className="text-xs text-muted-foreground">{setup.reason}</p>

        {setup.stance !== "AVOID" && setup.entry !== undefined ? (
          <>
            <table className="w-full text-xs border-collapse">
              <thead>
                <tr className="border-b border-border/50">
                  <th className="text-left text-[10px] font-bold text-muted-foreground uppercase py-1.5 pr-3">Level</th>
                  <th className="text-right text-[10px] font-bold text-muted-foreground uppercase py-1.5 pr-3">Price</th>
                  <th className="text-right text-[10px] font-bold text-muted-foreground uppercase py-1.5">Notes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/30">
                <tr>
                  <td className="py-1.5 pr-3 font-bold text-foreground">Entry</td>
                  <td className="py-1.5 pr-3 text-right font-mono font-bold text-foreground">${fmt(setup.entry)}</td>
                  <td className="py-1.5 text-right text-muted-foreground">{setup.entryNote}</td>
                </tr>
                {setup.tp1 !== undefined && (
                  <tr>
                    <td className="py-1.5 pr-3 font-bold text-emerald-600 dark:text-emerald-400">TP1</td>
                    <td className="py-1.5 pr-3 text-right font-mono font-bold text-emerald-600 dark:text-emerald-400">${fmt(setup.tp1)}</td>
                    <td className="py-1.5 text-right text-muted-foreground">+{(((setup.tp1 - setup.entry) / setup.entry) * 100).toFixed(1)}% from entry</td>
                  </tr>
                )}
                {setup.tp2 !== undefined && (
                  <tr>
                    <td className="py-1.5 pr-3 font-bold text-emerald-600 dark:text-emerald-400">TP2</td>
                    <td className="py-1.5 pr-3 text-right font-mono font-bold text-emerald-600 dark:text-emerald-400">${fmt(setup.tp2)}</td>
                    <td className="py-1.5 text-right text-muted-foreground">+{(((setup.tp2 - setup.entry!) / setup.entry!) * 100).toFixed(1)}% from entry</td>
                  </tr>
                )}
                {setup.maxTarget !== undefined && setup.entry !== undefined && (
                  <tr>
                    <td className="py-1.5 pr-3 font-bold text-violet-600 dark:text-violet-400">Max Target</td>
                    <td className="py-1.5 pr-3 text-right font-mono font-bold text-violet-600 dark:text-violet-400">${fmt(setup.maxTarget)}</td>
                    <td className="py-1.5 text-right text-muted-foreground">+{(((setup.maxTarget - setup.entry) / setup.entry) * 100).toFixed(1)}% from entry</td>
                  </tr>
                )}
                {setup.sl !== undefined && (
                  <tr>
                    <td className="py-1.5 pr-3 font-bold text-rose-600 dark:text-rose-400">Cut Loss</td>
                    <td className="py-1.5 pr-3 text-right font-mono font-bold text-rose-600 dark:text-rose-400">${fmt(setup.sl)}</td>
                    <td className="py-1.5 text-right text-muted-foreground">{(((setup.entry - setup.sl) / setup.entry) * 100).toFixed(1)}% below entry</td>
                  </tr>
                )}
              </tbody>
            </table>

            <div className="flex gap-4 text-[11px] text-muted-foreground">
              {setup.rr1 !== undefined && (
                <span>
                  RR to TP1: <span className={cn("font-bold", setup.rr1 >= 1.5 ? "text-emerald-600 dark:text-emerald-400" : "text-amber-600 dark:text-amber-400")}>
                    {setup.rr1.toFixed(1)}:1
                  </span>
                  {setup.rr1 < 1.5 && " ⚠ tight"}
                </span>
              )}
              {setup.rr2 !== undefined && (
                <span>
                  RR to TP2: <span className="font-bold text-emerald-600 dark:text-emerald-400">{setup.rr2.toFixed(1)}:1</span>
                </span>
              )}
            </div>
          </>
        ) : setup.stance === "AVOID" ? (
          <div className="flex gap-2 p-3 rounded-lg bg-rose-500/5 border border-rose-500/20">
            <AlertTriangle size={13} className="text-rose-500 shrink-0 mt-0.5" />
            <p className="text-[11px] text-rose-700 dark:text-rose-300">{setup.entryNote}</p>
          </div>
        ) : null}
      </div>

      {/* ── Key Levels ──────────────────────────────────────────────── */}
      <div className="p-5 space-y-3">
        <SectionTitle icon={<BarChart2 size={13} />}>Key Levels</SectionTitle>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <div className="text-[10px] font-bold uppercase text-rose-600 dark:text-rose-400 mb-2">Resistance</div>
            {levels.resistances.length === 0 ? (
              <p className="text-[11px] text-muted-foreground italic">Price above all tracked resistance</p>
            ) : levels.resistances.map((r) => (
              <div key={r.label} className="p-2 rounded bg-rose-500/5 border border-rose-500/20">
                <div className="flex justify-between items-baseline">
                  <span className="text-[10px] font-bold text-rose-700 dark:text-rose-400">{r.label}</span>
                  <span className="font-mono text-xs font-bold text-foreground">${fmt(r.price)}</span>
                </div>
                <p className="text-[9px] text-muted-foreground mt-0.5">{r.note}</p>
              </div>
            ))}
          </div>

          <div className="space-y-1.5">
            <div className="text-[10px] font-bold uppercase text-emerald-600 dark:text-emerald-400 mb-2">Support</div>
            {levels.supports.map((s) => (
              <div key={s.label} className="p-2 rounded bg-emerald-500/5 border border-emerald-500/20">
                <div className="flex justify-between items-baseline">
                  <span className="text-[10px] font-bold text-emerald-700 dark:text-emerald-400">{s.label}</span>
                  <span className="font-mono text-xs font-bold text-foreground">${fmt(s.price)}</span>
                </div>
                <p className="text-[9px] text-muted-foreground mt-0.5">{s.note}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Invalidation lines */}
        <div className="p-3 rounded-lg bg-muted/20 border border-border/50 space-y-1.5 text-[11px]">
          <div className="font-bold text-[10px] uppercase text-muted-foreground tracking-wider mb-1.5">Invalidation</div>
          <div className="flex gap-2">
            <span className="text-emerald-600 dark:text-emerald-400 font-bold shrink-0">Bull:</span>
            <span className="text-muted-foreground">
              Invalid below <span className="font-mono font-bold text-foreground">${fmt(titan.indicators.supertrend)}</span> (SuperTrend break on 4H close)
            </span>
          </div>
          {levels.resistances[levels.resistances.length - 1] && (
            <div className="flex gap-2">
              <span className="text-rose-600 dark:text-rose-400 font-bold shrink-0">Bear:</span>
              <span className="text-muted-foreground">
                Invalid above <span className="font-mono font-bold text-foreground">${fmt(levels.resistances[levels.resistances.length - 1].price)}</span> ({levels.resistances[levels.resistances.length - 1].label} reclaim)
              </span>
            </div>
          )}
        </div>
      </div>

      {/* ── Signal Track Record ───────────────────────────────────── */}
      <SignalTrackRecord symbol={oracle.symbol} currentPrice={price} />

    </div>
  );
}

// ─── Modal shell ─────────────────────────────────────────────────────────────

function CoinAnalysisModalComponent({ isOpen, onClose, symbol, timeframe, oracle }: CoinAnalysisModalProps) {
  const [mounted, setMounted] = useState(false);
  const { data: titan, isLoading: titanLoading } = useStrategyTitan(symbol, "4h");

  useEffect(() => { setMounted(true); }, []);
  useEffect(() => {
    if (!isOpen) return;
    const handleKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [isOpen, onClose]);

  if (!mounted || !isOpen) return null;

  const base = symbol.replace("/USDT", "");
  const price = oracle.price;

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div className="relative z-10 w-full max-w-2xl max-h-[90vh] flex flex-col bg-background border border-border rounded-xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-border bg-muted/50 shrink-0">
          <div className="flex items-center gap-3">
            <Zap size={16} className="text-amber-500" />
            <div>
              <div className="font-bold text-foreground">{base} Deep Analysis</div>
              <div className="text-[11px] text-muted-foreground flex items-center gap-2">
                <span>Oracle {oracle.micro_tf}/{oracle.macro_tf} · Titan 4H · ${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 })}</span>
                {oracle.last_updated && (
                  <span className="border-l border-border pl-2 opacity-70">
                    Last Analyzed: {new Date(oracle.last_updated).toLocaleTimeString()}
                  </span>
                )}
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-muted transition-colors text-muted-foreground hover:text-foreground"
          >
            <X size={16} />
          </button>
        </div>

        {/* Scrollable body */}
        <div className="overflow-y-auto flex-1 scrollbar-thin scrollbar-thumb-muted">
          {titanLoading ? (
            <div className="flex items-center justify-center py-16 text-sm text-muted-foreground">
              <div className="flex flex-col items-center gap-3">
                <div className="w-6 h-6 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
                Loading Titan data…
              </div>
            </div>
          ) : titan ? (
            <AnalysisBody oracle={oracle} titan={titan} price={price} />
          ) : (
            <div className="flex items-center justify-center py-16 text-sm text-muted-foreground">
              Failed to load Titan data.
            </div>
          )}
        </div>
      </div>
    </div>,
    document.body
  );
}

export const CoinAnalysisModal = CoinAnalysisModalComponent;
