"use client";

import { useTradeHistory } from "@/hooks/useTradingData";
import { Position } from "@/lib/api";
import { formatPriceCompact, duration } from "@/lib/formatters";
import { cn } from "@/lib/utils";
import { ChevronRight } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { TradeDetailModal } from "./TradeDetailModal";

const ROW_GRID = "grid grid-cols-6 items-center gap-0 py-2.5 px-4 border-b border-border/20 last:border-0";

function HistoryRow({ pos, onClick }: { pos: Position; onClick: () => void }) {
  const base = pos.symbol.replace("USDT", "");
  const isWin = pos.outcome === "WIN";
  const isLoss = pos.outcome === "LOSS";
  const isExpired = pos.outcome === "EXPIRED";
  const entry = pos.actual_entry ?? pos.intended_entry;
  const exit = pos.actual_exit ?? 0;

  return (
    <div className={cn(ROW_GRID, "hover:bg-secondary/20 transition-colors cursor-pointer")} onClick={onClick}>
      {/* Outcome badge */}
      <span className={cn(
        "text-[9px] font-black px-1.5 py-0.5 rounded uppercase text-center justify-self-start",
        isWin && "bg-emerald-500/10 text-emerald-500",
        isLoss && "bg-red-500/10 text-red-500",
        isExpired && "bg-muted text-muted-foreground",
      )}>
        {pos.outcome ?? "—"}
      </span>

      {/* Symbol + direction */}
      <div className="flex items-center gap-1.5">
        <Link href={`/chart/${base}-USDT`} className="font-black text-[13px] hover:underline">{base}</Link>
        <span className={cn(
          "text-[9px] font-black px-1 py-0.5 rounded",
          pos.direction === "LONG" ? "bg-emerald-500/10 text-emerald-500" : "bg-red-500/10 text-red-500"
        )}>{pos.direction}</span>
      </div>

      {/* Entry */}
      <span className="text-[11px] font-mono text-muted-foreground">${formatPriceCompact(entry)}</span>

      {/* Exit */}
      <span className="text-[11px] font-mono text-foreground">{exit > 0 ? `$${formatPriceCompact(exit)}` : "—"}</span>

      {/* PnL */}
      <span className={cn(
        "text-[12px] font-medium font-mono text-right",
        pos.pnl_usd !== null && pos.pnl_usd > 0 && "text-emerald-500",
        pos.pnl_usd !== null && pos.pnl_usd < 0 && "text-red-500",
        (pos.pnl_usd === null || isExpired) && "text-muted-foreground",
      )}>
        {pos.pnl_usd !== null ? `${pos.pnl_usd >= 0 ? "+" : ""}$${pos.pnl_usd.toFixed(2)}` : "—"}
        {pos.pnl_pct !== null && (
          <span className="text-[9px] ml-1 font-bold">({pos.pnl_pct >= 0 ? "+" : ""}{pos.pnl_pct.toFixed(1)}%)</span>
        )}
      </span>

      {/* Duration */}
      <span className="text-[10px] text-muted-foreground text-right">
        {duration(pos.filled_at, pos.closed_at)}
      </span>
    </div>
  );
}

export function TradeHistory() {
  const PAGE_SIZE = 20;
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
          <div className={cn(ROW_GRID, "py-1.5 text-[9px] font-bold text-muted-foreground uppercase tracking-wider")}>
            <span>Result</span>
            <span>Symbol</span>
            <span>Entry</span>
            <span>Exit</span>
            <span className="text-right">PnL</span>
            <span className="text-right">Held</span>
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
