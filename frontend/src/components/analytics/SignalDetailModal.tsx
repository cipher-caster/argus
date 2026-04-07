"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { X, Target, Zap, Clock, BarChart2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { SignalLogItem } from "@/lib/api";
import { formatPriceCompact, formatDateTime } from "@/lib/formatters";
import { OUTCOME_STYLE, OUTCOME_EMOJI } from "@/lib/outcomeConfig";

// ─── Props ──────────────────────────────────────────────────────────────────

interface SignalDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  signal: SignalLogItem | null;
}

// ─── Helpers ────────────────────────────────────────────────────────────────

function pctDistance(from: number, to: number) {
  return ((Math.abs(to - from) / from) * 100).toFixed(2);
}

const SOURCE_STYLE: Record<string, string> = {
  live: "text-sky-500 bg-sky-500/10 border-sky-500/20",
  scanner: "text-violet-500 bg-violet-500/10 border-violet-500/20",
  backtest: "text-amber-500 bg-amber-500/10 border-amber-500/20",
};

// ─── Sub-components ─────────────────────────────────────────────────────────

function SectionTitle({ icon, children }: { icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2 mb-3">
      <span className="text-muted-foreground">{icon}</span>
      <span className="text-[11px] font-bold uppercase tracking-widest text-muted-foreground">{children}</span>
    </div>
  );
}

function StatCard({ label, value, valueClass }: { label: string; value: string; valueClass?: string }) {
  return (
    <div className="bg-muted/30 border border-border/50 rounded-lg p-2">
      <div className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground mb-0.5">{label}</div>
      <div className={cn("text-xs font-mono font-medium", valueClass ?? "text-foreground")}>{value}</div>
    </div>
  );
}

function ProgressBar({ value, max, color }: { value: number; max: number; color: string }) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div className="h-1.5 rounded-full bg-secondary/60 flex-1 overflow-hidden">
      <div className={cn("h-full rounded-full", color)} style={{ width: `${pct}%` }} />
    </div>
  );
}

// ─── Modal body ─────────────────────────────────────────────────────────────

function DetailBody({ signal }: { signal: SignalLogItem }) {
  const isLong = signal.direction === "LONG";
  const tpDist = pctDistance(signal.entry, signal.tp);
  const slDist = pctDistance(signal.entry, signal.sl);
  const rr = (Math.abs(signal.tp - signal.entry) / Math.abs(signal.entry - signal.sl)).toFixed(2);

  const nowMs = Date.now();
  const durationSinceFired = nowMs - signal.fired_at;

  return (
    <div className="divide-y divide-border">
      {/* ── Price Levels ──────────────────────────────────────────── */}
      <div className="p-5 space-y-3">
        <SectionTitle icon={<Target size={13} />}>Price Levels</SectionTitle>

        <div className="grid grid-cols-3 gap-2">
          <StatCard label="Entry" value={`$${formatPriceCompact(signal.entry)}`} />
          <StatCard label={`TP (${tpDist}%)`} value={`$${formatPriceCompact(signal.tp)}`} valueClass="text-emerald-600 dark:text-emerald-400" />
          <StatCard label={`SL (${slDist}%)`} value={`$${formatPriceCompact(signal.sl)}`} valueClass="text-red-600 dark:text-red-400" />
        </div>

        <div className="flex items-center gap-3">
          <div className="bg-muted/30 border border-border/50 rounded-lg px-3 py-1.5">
            <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground mr-2">R:R</span>
            <span className={cn("text-xs font-mono font-medium", parseFloat(rr) >= 1.5 ? "text-emerald-600 dark:text-emerald-400" : "text-amber-600 dark:text-amber-400")}>
              {rr}:1
            </span>
          </div>

          {signal.resolved_price !== null && (
            <div className="bg-muted/30 border border-border/50 rounded-lg px-3 py-1.5">
              <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground mr-2">Resolved @</span>
              <span className="text-xs font-mono font-medium text-foreground">${formatPriceCompact(signal.resolved_price)}</span>
            </div>
          )}
        </div>
      </div>

      {/* ── Strategy ──────────────────────────────────────────────── */}
      <div className="p-5 space-y-3">
        <SectionTitle icon={<Zap size={13} />}>Strategy</SectionTitle>

        <div className="flex items-center gap-2 flex-wrap">
          <span className={cn(
            "text-[10px] font-black px-2 py-0.5 rounded border uppercase tracking-wider",
            signal.titan_signal.includes("BUY") ? "text-emerald-500 bg-emerald-500/10 border-emerald-500/20" :
            signal.titan_signal.includes("SELL") ? "text-red-500 bg-red-500/10 border-red-500/20" :
            "text-zinc-500 bg-zinc-500/10 border-zinc-500/20"
          )}>
            {signal.titan_signal.replace(/_/g, " ")}
          </span>
        </div>

        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground w-28 shrink-0">Titan Confidence</span>
            <ProgressBar value={signal.titan_confidence} max={100} color={signal.titan_confidence >= 60 ? "bg-emerald-500" : signal.titan_confidence >= 40 ? "bg-amber-500" : "bg-red-500"} />
            <span className="text-xs font-mono font-medium text-foreground w-10 text-right">{signal.titan_confidence}%</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground w-28 shrink-0">Conviction</span>
            <ProgressBar value={signal.conviction} max={100} color={signal.conviction >= 60 ? "bg-emerald-500" : signal.conviction >= 40 ? "bg-amber-500" : "bg-red-500"} />
            <span className="text-xs font-mono font-medium text-foreground w-10 text-right">{signal.conviction}</span>
          </div>
        </div>

        <div className="bg-muted/30 border border-border/50 rounded-lg p-2">
          <div className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground mb-1">Fired Reason</div>
          <div className="text-xs text-muted-foreground leading-relaxed">{signal.fired_reason}</div>
        </div>
      </div>

      {/* ── Timing ────────────────────────────────────────────────── */}
      <div className="p-5 space-y-3">
        <SectionTitle icon={<Clock size={13} />}>Timing</SectionTitle>

        <div className="grid grid-cols-2 gap-2">
          <StatCard label="Fired At" value={formatDateTime(signal.fired_at)} />
          <StatCard
            label="Resolved At"
            value={signal.resolved_at ? formatDateTime(signal.resolved_at) : "Still open"}
            valueClass={signal.resolved_at ? "text-foreground" : "text-sky-500"}
          />
          {signal.time_to_resolution_ms !== null && (
            <StatCard
              label="Time to Resolution"
              value={`${(signal.time_to_resolution_ms / 3_600_000).toFixed(1)}h`}
            />
          )}
          {signal.outcome === "OPEN" && (
            <StatCard
              label="Duration (open)"
              value={`${(durationSinceFired / 3_600_000).toFixed(1)}h`}
              valueClass="text-sky-500"
            />
          )}
        </div>
      </div>

      {/* ── Market Context ────────────────────────────────────────── */}
      <div className="p-5 space-y-3">
        <SectionTitle icon={<BarChart2 size={13} />}>Market Context</SectionTitle>

        <div className="grid grid-cols-2 gap-2">
          <StatCard label="Market State" value={signal.market_state || "\u2014"} />
          <div className="bg-muted/30 border border-border/50 rounded-lg p-2">
            <div className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground mb-0.5">Source</div>
            <span className={cn(
              "text-[10px] font-black px-2 py-0.5 rounded border uppercase tracking-wider",
              SOURCE_STYLE[signal.source] ?? "text-zinc-500 bg-zinc-500/10 border-zinc-500/20"
            )}>
              {signal.source}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <StatCard label="Entry Regime" value={signal.regime_at_signal || "\u2014"} />
          <StatCard label="Resolution Regime" value={signal.regime_at_resolution || "\u2014"} />
          <StatCard
            label="Entry BTC Price"
            value={signal.btc_price_at_signal ? `$${formatPriceCompact(signal.btc_price_at_signal)}` : "\u2014"}
          />
          <StatCard
            label="Resolution BTC Price"
            value={signal.btc_price_at_resolution ? `$${formatPriceCompact(signal.btc_price_at_resolution)}` : "\u2014"}
          />
        </div>

        {signal.regime_at_signal && signal.regime_at_resolution && signal.regime_at_signal !== signal.regime_at_resolution && (
          <div className="text-[11px] text-muted-foreground">
            Regime shift: {signal.regime_at_signal} &rarr; {signal.regime_at_resolution}
          </div>
        )}

        {signal.rejection_reason && (
          <div className="bg-red-500/5 border border-red-500/20 rounded-lg p-2">
            <div className="text-[10px] font-bold uppercase tracking-widest text-red-500 mb-1">Rejection Reason</div>
            <div className="text-xs text-muted-foreground leading-relaxed">{signal.rejection_reason}</div>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Modal shell ────────────────────────────────────────────────────────────

export function SignalDetailModal({ isOpen, onClose, signal }: SignalDetailModalProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => { setMounted(true); }, []);

  useEffect(() => {
    if (!isOpen) return;
    const handleKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [isOpen, onClose]);

  if (!mounted || !isOpen || !signal) return null;

  const base = signal.symbol.replace("USDT", "");
  const isLong = signal.direction === "LONG";

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      <div className="relative z-10 w-full max-w-lg max-h-[85vh] flex flex-col bg-background border border-border rounded-xl shadow-2xl overflow-hidden">
        {/* ── Header ──────────────────────────────────────────────── */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-border bg-muted/50 shrink-0">
          <div className="flex items-center gap-2">
            <span className="font-bold text-foreground">{base}</span>
            <span className={cn(
              "text-[10px] font-black px-1.5 py-0.5 rounded",
              isLong ? "bg-emerald-500/10 text-emerald-500" : "bg-red-500/10 text-red-500"
            )}>
              {signal.direction}
            </span>
            <span className={cn(
              "text-[10px] font-black px-1.5 py-0.5 rounded border",
              OUTCOME_STYLE[signal.outcome] ?? OUTCOME_STYLE.OPEN
            )}>
              {signal.outcome} {OUTCOME_EMOJI[signal.outcome] ?? ""}
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-muted transition-colors text-muted-foreground hover:text-foreground"
          >
            <X size={16} />
          </button>
        </div>

        {/* ── Body ────────────────────────────────────────────────── */}
        <div className="overflow-y-auto flex-1 scrollbar-thin scrollbar-thumb-muted">
          <DetailBody signal={signal} />
        </div>
      </div>
    </div>,
    document.body
  );
}
