"use client";

import { useActivePositions, useClosePosition } from "@/hooks/useTradingData";
import { Position } from "@/lib/api";
import { cn } from "@/lib/utils";
import { formatPriceCompact, timeAgo } from "@/lib/formatters";
import { X } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { TradeDetailModal } from "./TradeDetailModal";

function StatusBadge({ status }: { status: Position["status"] }) {
  return (
    <span className={cn(
      "text-[9px] font-black px-1.5 py-0.5 rounded uppercase tracking-wide",
      status === "OPEN" && "bg-emerald-500/10 text-emerald-500",
      status === "PENDING" && "bg-yellow-500/10 text-yellow-500",
    )}>
      {status === "PENDING" ? "Pending" : "Open"}
    </span>
  );
}

const ROW_GRID = "grid grid-cols-[repeat(8,1fr)_40px] items-center gap-x-2 py-2.5 px-4 border-b border-border/20 last:border-0";

function PositionRow({ pos, onClose, onClick }: { pos: Position; onClose: (id: number) => void; onClick: () => void }) {
  const base = pos.symbol.replace("USDT", "");
  const isLong = pos.direction === "LONG";
  const entry = pos.actual_entry ?? pos.intended_entry;
  const pnlPct = pos.unrealized_pnl_pct;

  return (
    <div className={cn(ROW_GRID, "hover:bg-secondary/20 transition-colors cursor-pointer")} onClick={onClick}>
      {/* Symbol + direction */}
      <div className="flex items-center gap-1.5">
        <Link href={`/chart/${base}-USDT`} className="font-black text-[13px] hover:underline">{base}</Link>
        <span className={cn(
          "text-[9px] font-black px-1 py-0.5 rounded",
          isLong ? "bg-emerald-500/10 text-emerald-500" : "bg-red-500/10 text-red-500"
        )}>{pos.direction}</span>
      </div>

      {/* Status */}
      <div className="flex"><StatusBadge status={pos.status} /></div>

      {/* Entry */}
      <span className="text-[11px] font-mono text-muted-foreground">${formatPriceCompact(entry)}</span>

      {/* Now */}
      <span className="text-[11px] font-mono text-foreground">
        {pos.current_price ? `$${formatPriceCompact(pos.current_price)}` : "—"}
      </span>

      {/* TP */}
      <span className="text-[11px] font-mono text-emerald-500/70">${formatPriceCompact(pos.intended_tp)}</span>

      {/* SL */}
      <span className="text-[11px] font-mono text-red-500/70">${formatPriceCompact(pos.intended_sl)}</span>

      {/* PnL */}
      <span className={cn(
        "text-[11px] font-medium font-mono text-right",
        pnlPct !== undefined && pnlPct !== null && pnlPct >= 0 ? "text-emerald-500" : "text-red-500",
        pnlPct === undefined || pnlPct === null ? "text-muted-foreground" : "",
      )}>
        {pnlPct !== undefined && pnlPct !== null
          ? `${pnlPct >= 0 ? "+" : ""}${pnlPct.toFixed(1)}%`
          : "—"}
      </span>

      {/* Size + age */}
      <div className="text-[10px] text-muted-foreground text-right">
        <div className="font-mono">${pos.quote_amount.toFixed(0)}</div>
        <div>{timeAgo(pos.created_at)}</div>
      </div>

      {/* Close button */}
      <button
        onClick={(e) => { e.stopPropagation(); onClose(pos.id); }}
        className="p-2 rounded hover:bg-red-500/10 text-muted-foreground hover:text-red-500 transition-colors justify-self-center"
        title="Close position"
      >
        <X size={14} />
      </button>
    </div>
  );
}

export function PositionsTable() {
  const { data, isLoading } = useActivePositions();
  const closePos = useClosePosition();
  const [selectedPosition, setSelectedPosition] = useState<Position | null>(null);

  const positions = data?.data ?? [];

  return (
    <div className="bg-card/60 backdrop-blur-md rounded-2xl border border-border/40 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-border/30">
        <h3 className="text-sm font-black tracking-tight">Active Positions</h3>
        {positions.length > 0 && (
          <span className="text-[10px] font-black px-1.5 py-0.5 rounded-full bg-primary/10 text-primary">
            {positions.length}
          </span>
        )}
      </div>

      {isLoading ? (
        <div className="h-24 flex items-center justify-center text-muted-foreground text-xs">Loading...</div>
      ) : positions.length === 0 ? (
        <div className="h-24 flex items-center justify-center text-muted-foreground text-xs">
          No active positions
        </div>
      ) : (
        <div>
          {/* Header */}
          <div className={cn(ROW_GRID, "py-1.5 text-[9px] font-bold text-muted-foreground uppercase tracking-wider")}>
            <span>Symbol</span>
            <span>Status</span>
            <span>Entry</span>
            <span>Now</span>
            <span>TP</span>
            <span>SL</span>
            <span className="text-right">PnL</span>
            <span className="text-right">Size / Age</span>
            <span />
          </div>
          {positions.map(p => (
            <PositionRow
              key={p.id}
              pos={p}
              onClose={(id) => closePos.mutate(id)}
              onClick={() => setSelectedPosition(p)}
            />
          ))}
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
