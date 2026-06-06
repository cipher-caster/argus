"use client";

import { useSignalLog } from "@/hooks/useAnalyticsData";
import { SignalLogItem } from "@/lib/api";
import { formatPriceCompact, timeAgo } from "@/lib/formatters";
import { cn } from "@/lib/utils";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Radio, ChevronRight } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { CardError } from "@/components/ui/CardError";
import Link from "next/link";

function SignalRow({ item }: { item: SignalLogItem }) {
  const base = item.symbol.replace("USDT", "");
  const isLong = item.direction === "LONG";

  return (
    <div className="flex items-center justify-between py-2.5 px-4 border-b border-border/20 last:border-0 hover:bg-secondary/20 transition-colors">
      {/* Left: symbol + direction */}
      <div className="flex items-center gap-2 min-w-[90px]">
        <Link href={`/chart/${base}-USDT`} className="font-black text-[13px] hover:underline">{base}</Link>
        <span className={cn(
          "text-[9px] font-black px-1.5 py-0.5 rounded",
          isLong ? "bg-emerald-500/10 text-emerald-500" : "bg-red-500/10 text-red-500"
        )}>
          {item.direction}
        </span>
      </div>
      {/* Middle: entry / TP / SL */}
      <div className="flex items-center gap-3 text-[11px] font-mono">
        <span className="text-muted-foreground w-[52px]">${formatPriceCompact(item.entry)}</span>
        <span className="text-emerald-500 w-[52px]">${formatPriceCompact(item.tp)}</span>
        <span className="text-red-500 w-[52px]">${formatPriceCompact(item.sl)}</span>
      </div>
      {/* Right: conviction + age */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1 w-[52px]">
          <div className="h-1.5 rounded-full bg-primary/30 w-10 overflow-hidden">
            <div className="h-full bg-primary rounded-full" style={{ width: `${item.conviction}%` }} />
          </div>
          <span className="text-[10px] font-bold text-muted-foreground">{item.conviction}</span>
        </div>
        <span className="text-[10px] text-muted-foreground w-[45px]">{timeAgo(item.fired_at)}</span>
      </div>
    </div>
  );
}

export function ActiveSignals() {
  const { data, isLoading, isError } = useSignalLog(undefined, "live", 50);
  const openSignals = data?.data.filter(s => s.outcome === "OPEN") ?? [];

  return (
    <div className="bg-secondary/30 border border-border/50 rounded-2xl overflow-hidden w-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border/30">
        <div className="flex items-center gap-2">
          <Radio size={14} className="text-primary" />
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <h3 className="text-sm font-black tracking-tight cursor-help">Active Signals</h3>
              </TooltipTrigger>
              <TooltipContent side="bottom" align="start" className="max-w-[240px] text-xs">
                Tracked positions — logged setups being monitored until TP, SL, or review deadline
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          {openSignals.length > 0 && (
            <span className="text-[10px] font-black px-1.5 py-0.5 rounded-full bg-primary/10 text-primary">
              {openSignals.length}
            </span>
          )}
        </div>
        <Link
          href="/analytics"
          className="flex items-center gap-1 text-[10px] text-muted-foreground hover:text-foreground transition-colors font-bold"
        >
          Signal Log <ChevronRight size={10} />
        </Link>
      </div>
      {/* Column headers */}
      {!isLoading && openSignals.length > 0 && (
        <div className="flex items-center justify-between px-4 py-1.5 border-b border-border/20 bg-secondary/20">
          <span className="text-[9px] font-black uppercase tracking-widest text-muted-foreground/50 min-w-[90px]">Symbol</span>
          <div className="flex items-center gap-3 text-[9px] font-black uppercase tracking-widest">
            <span className="text-muted-foreground/50 w-[52px]">Entry</span>
            <span className="text-emerald-500/50 w-[52px]">TP</span>
            <span className="text-red-500/50 w-[52px]">SL</span>
          </div>
          <div className="flex items-center gap-3 text-[9px] font-black uppercase tracking-widest">
            <span className="text-muted-foreground/50 w-[52px]">Conv.</span>
            <span className="text-muted-foreground/50 w-[45px]">Age</span>
          </div>
        </div>
      )}
      {/* Body */}
      {isLoading ? (
        <div className="divide-y divide-border/20">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="flex items-center justify-between py-2.5 px-4">
              <div className="flex items-center gap-2 min-w-[90px]">
                <Skeleton className="w-10 h-3.5" />
                <Skeleton className="w-8 h-4 rounded" />
              </div>
              <div className="flex items-center gap-3">
                <Skeleton className="w-[52px] h-3" />
                <Skeleton className="w-[52px] h-3" />
                <Skeleton className="w-[52px] h-3" />
              </div>
              <div className="flex items-center gap-3">
                <Skeleton className="w-[52px] h-3" />
                <Skeleton className="w-[45px] h-3" />
              </div>
            </div>
          ))}
        </div>
      ) : isError ? (
        <div className="h-24 flex items-center justify-center"><CardError /></div>
      ) : openSignals.length === 0 ? (
        <div className="h-24 flex items-center justify-center text-muted-foreground text-xs">
          No active signals — waiting for setups
        </div>
      ) : (
        <div>
          {openSignals.map(s => <SignalRow key={s.id} item={s} />)}
        </div>
      )}
    </div>
  );
}
