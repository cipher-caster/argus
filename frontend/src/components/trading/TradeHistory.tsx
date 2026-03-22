"use client";

import { useTradeHistory } from "@/hooks/useTradingData";
import { Position } from "@/lib/api";
import { cn } from "@/lib/utils";
import { ChevronRight } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { TradeDetailModal } from "./TradeDetailModal";

function formatPrice(p: number) {
  if (p >= 1000) return p.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  if (p >= 1) return p.toFixed(4);
  return p.toFixed(6);
}

function duration(from: number | null, to: number | null): string {
  if (!from || !to) return "—";
  const ms = to - from;
  const h = Math.floor(ms / 3_600_000);
  const d = Math.floor(ms / 86_400_000);
  if (d >= 1) return `${d}d ${h % 24}h`;
  if (h >= 1) return `${h}h`;
  return "< 1h";
}

function HistoryRow({ pos, onClick }: { pos: Position; onClick: () => void }) {
  const base = pos.symbol.replace("USDT", "");
  const isWin = pos.outcome === "WIN";
  const isLoss = pos.outcome === "LOSS";
  const isExpired = pos.outcome === "EXPIRED";
  const entry = pos.actual_entry ?? pos.intended_entry;
  const exit = pos.actual_exit ?? 0;

  return (
    <div className="flex items-center gap-3 py-2.5 px-4 border-b border-border/20 last:border-0 hover:bg-secondary/20 transition-colors cursor-pointer" onClick={onClick}>
      {/* Outcome badge */}
      <span className={cn(
        "text-[9px] font-black px-1.5 py-0.5 rounded uppercase w-10 text-center",
        isWin && "bg-emerald-500/10 text-emerald-500",
        isLoss && "bg-red-500/10 text-red-500",
        isExpired && "bg-muted text-muted-foreground",
      )}>
        {pos.outcome ?? "—"}
      </span>

      {/* Symbol + direction */}
      <div className="flex items-center gap-1.5 min-w-[70px]">
        <Link href={`/chart/${base}-USDT`} className="font-black text-[13px] hover:underline">{base}</Link>
        <span className={cn(
          "text-[9px] font-black px-1 py-0.5 rounded",
          pos.direction === "LONG" ? "bg-emerald-500/10 text-emerald-500" : "bg-red-500/10 text-red-500"
        )}>{pos.direction}</span>
      </div>

      {/* Entry → Exit */}
      <div className="flex items-center gap-1.5 text-[11px] font-mono text-muted-foreground flex-1">
        <span>${formatPrice(entry)}</span>
        <span className="text-muted-foreground/40">→</span>
        <span className="text-foreground">${exit > 0 ? formatPrice(exit) : "—"}</span>
      </div>

      {/* PnL */}
      <span className={cn(
        "text-[12px] font-black font-mono min-w-[70px] text-right",
        isWin && "text-emerald-500",
        isLoss && "text-red-500",
        isExpired && "text-muted-foreground",
      )}>
        {pos.pnl_usd !== null ? `${pos.pnl_usd >= 0 ? "+" : ""}$${pos.pnl_usd.toFixed(2)}` : "—"}
        {pos.pnl_pct !== null && (
          <span className="text-[9px] ml-1 font-bold">({pos.pnl_pct >= 0 ? "+" : ""}{pos.pnl_pct.toFixed(1)}%)</span>
        )}
      </span>

      {/* Duration */}
      <span className="text-[10px] text-muted-foreground min-w-[40px] text-right">
        {duration(pos.filled_at, pos.closed_at)}
      </span>
    </div>
  );
}

export function TradeHistory() {
  const PAGE_SIZE = 50;
  const [page, setPage] = useState(1);
  const [selectedPosition, setSelectedPosition] = useState<Position | null>(null);
  const offset = (page - 1) * PAGE_SIZE;
  const { data, isLoading } = useTradeHistory(PAGE_SIZE, offset);
  const trades = data?.data ?? [];
  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 1;

  return (
    <div className="bg-card/60 backdrop-blur-md rounded-2xl border border-border/40 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-border/30">
        <h3 className="text-sm font-black tracking-tight">Trade History</h3>
        {data && data.total > 0 && (
          <span className="text-[10px] text-muted-foreground">{data.total} closed</span>
        )}
      </div>

      {isLoading ? (
        <div className="h-24 flex items-center justify-center text-muted-foreground text-xs">Loading...</div>
      ) : trades.length === 0 ? (
        <div className="h-24 flex items-center justify-center text-muted-foreground text-xs">
          No closed trades yet
        </div>
      ) : (
        <div>
          <div className="flex items-center gap-3 py-1.5 px-4 border-b border-border/20 text-[9px] font-bold text-muted-foreground uppercase tracking-wider">
            <span className="w-10">Result</span>
            <span className="min-w-[70px]">Symbol</span>
            <span className="flex-1">Entry → Exit</span>
            <span className="min-w-[70px] text-right">PnL</span>
            <span className="min-w-[40px] text-right">Held</span>
          </div>
          {trades.map(t => <HistoryRow key={t.id} pos={t} onClick={() => setSelectedPosition(t)} />)}

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-4 py-4 border-t border-border/30">
              <div className="flex items-center gap-1 bg-muted/30 p-1 rounded-xl border border-border/50">
                <button
                  className="px-3 py-1.5 text-xs font-bold rounded-lg hover:bg-muted transition-all disabled:opacity-30 disabled:pointer-events-none"
                  onClick={() => setPage(1)}
                  disabled={page === 1}
                >
                  First
                </button>
                <button
                  className="px-3 py-1.5 text-xs font-bold rounded-lg hover:bg-muted transition-all disabled:opacity-30 disabled:pointer-events-none flex items-center gap-1"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  <ChevronRight size={12} className="rotate-180" /> Prev
                </button>
                <div className="px-4 text-xs font-bold border-x border-border/50">
                  <span className="text-muted-foreground">Page </span>
                  <span>{page}</span>
                  <span className="text-muted-foreground"> / {totalPages}</span>
                </div>
                <button
                  className="px-3 py-1.5 text-xs font-bold rounded-lg hover:bg-muted transition-all disabled:opacity-30 disabled:pointer-events-none flex items-center gap-1"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                >
                  Next <ChevronRight size={12} />
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      <TradeDetailModal
        isOpen={selectedPosition !== null}
        onClose={() => setSelectedPosition(null)}
        position={selectedPosition}
      />
    </div>
  );
}
