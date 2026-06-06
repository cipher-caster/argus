"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { X, Target, TrendingUp, TrendingDown, ShieldAlert, Zap, AlertTriangle, BarChart2, Activity } from "lucide-react";
import { cn } from "@/lib/utils";
import { TitanStrategyResponse } from "@/lib/api";
import { useBacktestStats, useSignalLog } from "@/hooks/useAnalyticsData";
import { Badge } from "@/components/ui/badge";


interface CoinAnalysisModalProps {
  isOpen: boolean;
  onClose: () => void;
  symbol: string;
  timeframe: string;
  titan: TitanStrategyResponse;
  regime: string;
}

// ─── Derivation helpers (regime + Titan, not Oracle) ──────────────────────

type Stance = "BUY" | "BUY_LIMIT" | "SELL" | "SELL_LIMIT" | "WAIT" | "AVOID";

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

function deriveSpotSetup(
  titan: TitanStrategyResponse,
  regime: string,
  price: number
): SpotSetup {
  const isLong = titan.signal === "BUY" || titan.signal === "BUY_LIMIT";
  const isShort = titan.signal === "SELL" || titan.signal === "SELL_LIMIT";
  const regimeAligned = (regime === "BULL" && isLong) || (regime === "BEAR" && isShort);

  if (isLong || isShort) {
    const entry = titan.targets.entry;
    const tp = titan.targets.tp;
    const sl = titan.targets.sl;
    const maxTarget = isLong ? tp * 1.3 : tp * 0.7;
    const rr = tp && sl ? Math.abs(tp - entry) / Math.abs(entry - sl) : undefined;

    const regTag = regimeAligned ? `with ${regime.toLowerCase()} trend` : `against ${regime.toLowerCase()} trend`;
    const reason = `Titan ${titan.signal.replace("_", " ")} (${regTag}) · ${titan.confidence}% confidence`;

    const useLimit = (isLong && entry < price) || (isShort && entry > price);

    return {
      stance: useLimit
        ? (isLong ? "BUY_LIMIT" : "SELL_LIMIT")
        : (isLong ? "BUY" : "SELL"),
      reason,
      entry,
      tp1: tp,
      tp2: undefined,
      maxTarget,
      sl,
      entryNote: useLimit
        ? `Limit ~${(((price - entry) / price) * 100).toFixed(1)}% from current`
        : "Market order",
      rr1: rr,
      rr2: undefined,
      rrMax: rr,
    };
  }

  // No signal — wait
  const ema20 = titan.indicators.ema20;
  const waitLevel = isLong ? ema20 : titan.targets.entry;
  return {
    stance: "WAIT",
    reason: `Titan no signal — wait for ${titan.trend === "BULLISH" ? "pullback to support" : "rejection at resistance"}`,
    entry: waitLevel,
    tp1: titan.targets.tp,
    tp2: undefined,
    maxTarget: undefined,
    sl: titan.targets.sl,
    rr1: undefined,
    rr2: undefined,
    rrMax: undefined,
    entryNote: `On confirmed close ${waitLevel > price ? "above" : "below"} $${waitLevel.toFixed(2)}`,
  };
}

interface KeyLevel { label: string; price: number; note: string }

function deriveKeyLevels(titan: TitanStrategyResponse, price: number) {
  const resistances: KeyLevel[] = [];
  const supports: KeyLevel[] = [];

  if (titan.indicators.ema20 > price)
    resistances.push({ label: "EMA20 (4H)", price: titan.indicators.ema20, note: "Immediate resistance" });
  if (titan.indicators.ema50 > price)
    resistances.push({ label: "EMA50 (4H)", price: titan.indicators.ema50, note: "Higher timeframe resistance" });

  if (titan.indicators.ema20 <= price)
    supports.push({ label: "EMA20 (4H)", price: titan.indicators.ema20, note: "Ideal limit entry zone" });
  if (titan.indicators.ema50 <= price)
    supports.push({ label: "EMA50 (4H)", price: titan.indicators.ema50, note: "First cushion" });
  supports.push({ label: "SuperTrend", price: titan.indicators.supertrend, note: "Trend floor — 4H close below = bearish flip" });

  return {
    resistances: resistances.sort((a, b) => a.price - b.price),
    supports: supports.sort((a, b) => b.price - a.price),
  };
}

function deriveSummary(
  titan: TitanStrategyResponse,
  regime: string,
  price: number,
  setup: SpotSetup,
  levels: ReturnType<typeof deriveKeyLevels>
): string {
  const base = titan.symbol.replace("/USDT", "");
  const situation = `${base} is at $${price.toFixed(2)} — ${regime} regime, Titan ${titan.trend} (${titan.confidence}% confidence).`;

  const bullTrigger = levels.resistances.length > 0
    ? `Bull trigger: break above $${levels.resistances[0].price.toFixed(2)} (${levels.resistances[0].label}) for continuation.`
    : `Price above all resistance — bull momentum confirmed.`;

  const bearTrigger = `Bear trigger: 4H close below SuperTrend at $${titan.indicators.supertrend.toFixed(2)} flips bearish.`;

  const action =
    setup.stance === "AVOID" ? `Avoid entries now. ${setup.entryNote}.`
    : setup.stance === "WAIT" ? `Set alert at $${setup.entry?.toFixed(2)} and wait for confirmation.`
    : `Place ${setup.stance.replace("_", " ").toLowerCase()} at $${setup.entry?.toFixed(2)}, cut loss at $${setup.sl?.toFixed(2)}.`;

  return [situation, bullTrigger, bearTrigger, action].join(" ");
}

// ─── Sub-components ────────────────────────────────────────────────────────

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
  if (stance === "SELL" || stance === "SELL_LIMIT")
    return "text-rose-700 dark:text-rose-400 bg-rose-500/10 border-rose-500/30";
  if (stance === "AVOID")
    return "text-rose-700 dark:text-rose-400 bg-rose-500/10 border-rose-500/30";
  return "text-amber-700 dark:text-amber-400 bg-amber-500/10 border-amber-500/30";
}

function SignalBadgeClass(signal: string) {
  if (signal.includes("BUY")) return "text-emerald-700 dark:text-emerald-400 bg-emerald-500/10 border-emerald-500/20";
  if (signal.includes("SELL")) return "text-rose-700 dark:text-rose-400 bg-rose-500/10 border-rose-500/20";
  return "text-slate-600 dark:text-slate-400 bg-slate-400/10 border-slate-400/20";
}

function fmt(n: number | undefined, digits = 2): string {
  if (n === undefined) return "—";
  return n.toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

// ─── Signal Track Record ───────────────────────────────────────────────────

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
  REJECTED: "text-zinc-500 bg-zinc-500/10",
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

      {coinStats && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
          {[
            { label: "Win Rate", value: `${wr}%`, cls: wr >= 45 ? "text-emerald-500" : wr >= 33 ? "text-amber-500" : "text-red-500" },
            { label: "Profit", value: `${coinStats.profit_r > 0 ? "+" : ""}${coinStats.profit_r}R`, cls: coinStats.profit_r > 0 ? "text-emerald-500" : "text-red-500" },
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
            <div className={cn("h-full rounded-full", wr >= 45 ? "bg-emerald-500" : wr >= 33 ? "bg-amber-500" : "bg-red-500")}
              style={{ width: `${wr}%` }} />
          </div>
          <span className={cn("text-[10px] font-black px-2 py-0.5 rounded-md",
            isProfitable ? "bg-emerald-500/10 text-emerald-500" : isMarginal ? "bg-amber-500/10 text-amber-500" : "bg-red-500/10 text-red-500"
          )}>
            {isProfitable ? "PROFITABLE" : isMarginal ? "MARGINAL" : "UNPROFITABLE"}
          </span>
        </div>
      )}

      {openSignals.length > 0 && (
        <div className="space-y-1.5">
          <div className="text-[10px] font-bold text-sky-500 uppercase tracking-wider">Active Signals</div>
          {openSignals.map((s) => {
            const isLong = s.direction === "LONG";
            const distToTp = isLong ? ((s.tp - currentPrice) / currentPrice * 100) : ((currentPrice - s.tp) / currentPrice * 100);
            const distToSl = isLong ? ((currentPrice - s.sl) / currentPrice * 100) : ((s.sl - currentPrice) / currentPrice * 100);
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
        <div className="text-center text-[11px] text-muted-foreground py-4">Loading signal history...</div>
      )}
    </div>
  );
}

// ─── Modal body ────────────────────────────────────────────────────────────

function AnalysisBody({ titan, price, regime }: {
  titan: TitanStrategyResponse;
  price: number;
  regime: string;
}) {
  const setup = deriveSpotSetup(titan, regime, price);
  const levels = deriveKeyLevels(titan, price);
  const summary = deriveSummary(titan, regime, price, setup, levels);
  const isLong = titan.signal === "BUY" || titan.signal === "BUY_LIMIT";
  const isShort = titan.signal === "SELL" || titan.signal === "SELL_LIMIT";
  const regimeAligned = (regime === "BULL" && isLong) || (regime === "BEAR" && isShort);

  return (
    <div className="divide-y divide-border">
      {/* ── Summary ─────────────────────────────────────────────────── */}
      <div className="p-5">
        <div className="flex items-center gap-2 mb-3">
          <span className={cn("text-[9px] font-black px-2 py-0.5 rounded uppercase tracking-wider",
            regime === "BULL" ? "bg-green-500/15 text-green-500" : "bg-red-500/15 text-red-500"
          )}>{regime}</span>
          {!regimeAligned && (isLong || isShort) && (
            <span className="text-[9px] font-black px-2 py-0.5 rounded bg-yellow-500/15 text-yellow-600 dark:text-yellow-400 uppercase tracking-wider">COUNTER-TREND</span>
          )}
        </div>
        <SectionTitle icon={<ShieldAlert size={13} />}>Summary</SectionTitle>
        <p className="text-[12px] leading-relaxed text-muted-foreground">{summary}</p>
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
            titan.trend === "BEARISH" ? "text-rose-600 dark:text-rose-400" : "text-muted-foreground"
          )}>{titan.trend}</span>
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
              <span className="text-xs font-mono font-medium text-foreground">{value}</span>
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
              <span className={cn("text-xs font-mono font-medium", color)}>{value}</span>
            </div>
          ))}
        </div>

        <div className="text-[10px] text-muted-foreground">
          Momentum: <span className="font-bold text-foreground">{titan.momentum.status}</span>
          {titan.momentum.is_overbought && " · Overbought"}
          {titan.momentum.is_oversold && " · Oversold"}
          {titan.momentum.macd_crossed !== "NONE" && ` · MACD crossed ${titan.momentum.macd_crossed}`}
        </div>
      </div>

      {/* ── Spot Setup ──────────────────────────────────────────────── */}
      <div className="p-5 space-y-3">
        <SectionTitle icon={<Target size={13} />}>Setup</SectionTitle>

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
                  <td className="py-1.5 pr-3 text-right font-mono font-medium text-foreground">${fmt(setup.entry)}</td>
                  <td className="py-1.5 text-right text-muted-foreground">{setup.entryNote}</td>
                </tr>
                {setup.tp1 !== undefined && (
                  <tr>
                    <td className="py-1.5 pr-3 font-bold text-emerald-600 dark:text-emerald-400">TP</td>
                    <td className="py-1.5 pr-3 text-right font-mono font-medium text-emerald-600 dark:text-emerald-400">${fmt(setup.tp1)}</td>
                    <td className="py-1.5 text-right text-muted-foreground">+{(((setup.tp1 - setup.entry) / setup.entry) * 100).toFixed(1)}% from entry</td>
                  </tr>
                )}
                {setup.sl !== undefined && (
                  <tr>
                    <td className="py-1.5 pr-3 font-bold text-rose-600 dark:text-rose-400">Cut Loss</td>
                    <td className="py-1.5 pr-3 text-right font-mono font-medium text-rose-600 dark:text-rose-400">${fmt(setup.sl)}</td>
                    <td className="py-1.5 text-right text-muted-foreground">{(((setup.entry - setup.sl) / setup.entry) * 100).toFixed(1)}% below entry</td>
                  </tr>
                )}
              </tbody>
            </table>

            {setup.rr1 !== undefined && (
              <div className="text-[11px] text-muted-foreground">
                R:R: <span className={cn("font-bold", setup.rr1 >= 1.5 ? "text-emerald-600 dark:text-emerald-400" : "text-amber-600 dark:text-amber-400")}>
                  {setup.rr1.toFixed(1)}:1
                </span>
                {setup.rr1 < 1.5 && " (tight)"}
              </div>
            )}
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
                  <span className="font-mono text-xs font-medium text-foreground">${fmt(r.price)}</span>
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
                  <span className="font-mono text-xs font-medium text-foreground">${fmt(s.price)}</span>
                </div>
                <p className="text-[9px] text-muted-foreground mt-0.5">{s.note}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="p-3 rounded-lg bg-muted/20 border border-border/50 space-y-1.5 text-[11px]">
          <div className="font-bold text-[10px] uppercase text-muted-foreground tracking-wider mb-1.5">Invalidation</div>
          <div className="flex gap-2">
            <span className="text-emerald-600 dark:text-emerald-400 font-bold shrink-0">
              {isLong ? "Long" : "Short"} invalid:
            </span>
            <span className="text-muted-foreground">
              {isLong
                ? <>Below <span className="font-mono font-medium text-foreground">${fmt(titan.indicators.supertrend)}</span> (SuperTrend)</>
                : <>Above <span className="font-mono font-medium text-foreground">${fmt(titan.targets.sl)}</span> (stop loss)</>
              }
            </span>
          </div>
        </div>
      </div>

      {/* ── Signal Track Record ───────────────────────────────────── */}
      <SignalTrackRecord symbol={titan.symbol} currentPrice={price} />
    </div>
  );
}

// ─── Modal shell ───────────────────────────────────────────────────────────

function CoinAnalysisModalComponent({ isOpen, onClose, symbol, timeframe, titan, regime }: CoinAnalysisModalProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => { setMounted(true); }, []);

  useEffect(() => {
    if (!isOpen) return;
    const handleKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [isOpen, onClose]);

  if (!mounted || !isOpen) return null;

  const base = symbol.replace("/USDT", "");
  const price = titan.targets.entry;

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      <div className="relative z-10 w-full max-w-2xl max-h-[90vh] flex flex-col bg-background border border-border rounded-xl shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-border bg-muted/50 shrink-0">
          <div className="flex items-center gap-3">
            <Zap size={16} className="text-amber-500" />
            <div>
              <div className="font-bold text-foreground">{base} Deep Analysis</div>
              <div className="text-[11px] text-muted-foreground flex items-center gap-2">
                <span>Titan 4H · ${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 })}</span>
              </div>
            </div>
          </div>
          <button onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-muted transition-colors text-muted-foreground hover:text-foreground">
            <X size={16} />
          </button>
        </div>

        <div className="overflow-y-auto flex-1 scrollbar-thin scrollbar-thumb-muted">
          <AnalysisBody titan={titan} price={price} regime={regime} />
        </div>
      </div>
    </div>,
    document.body
  );
}

export const CoinAnalysisModal = CoinAnalysisModalComponent;
