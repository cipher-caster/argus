"use client";

import { useActivePositions, useClosePosition } from "@/hooks/useTradingData";
import { Position } from "@/lib/api";
import { cn } from "@/lib/utils";
import { formatPriceCompact } from "@/lib/formatters";
import { X } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { TradeDetailModal } from "./TradeDetailModal";

// formatPriceCompact imported from @/lib/formatters

function timeAgo(ms: number) {
  const diff = Date.now() - ms;
  const h = Math.floor(diff / 3_600_000);
  const d = Math.floor(diff / 86_400_000);
  if (d >= 1) return `${d}d`;
  if (h >= 1) return `${h}h`;
  return "< 1h";
}

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

function PositionRow({ pos, onClose, onClick }: { pos: Position; onClose: (id: number) => void; onClick: () => void }) {
  const base = pos.symbol.replace("USDT", "");
  const isLong = pos.direction === "LONG";
  const entry = pos.actual_entry ?? pos.intended_entry;
  const hasPnl = pos.unrealized_pnl_pct !== undefined;

  return (
    <div className="flex items-center gap-3 py-2.5 px-4 border-b border-border/20 last:border-0 hover:bg-secondary/20 transition-colors cursor-pointer" onClick={onClick}>
      {/* Symbol + direction */}
      <div className="flex items-center gap-1.5 min-w-[70px]">
        <Link href={`/chart/${base}-USDT`} className="font-black text-[13px] hover:underline">{base}</Link>
        <span className={cn(
          "text-[9px] font-black px-1 py-0.5 rounded",
          isLong ? "bg-emerald-500/10 text-emerald-500" : "bg-red-500/10 text-red-500"
        )}>{pos.direction}</span>
      </div>

      {/* Status */}
      <StatusBadge status={pos.status} />

      {/* Entry / TP / SL */}
      <div className="flex items-center gap-2.5 text-[11px] font-mono flex-1">
        <span className="text-muted-foreground">${formatPriceCompact(entry)}</span>
        {pos.current_price && (
          <>
            <span className="text-muted-foreground/40">→</span>
            <span className="text-foreground">${formatPriceCompact(pos.current_price)}</span>
          </>
        )}
        <span className="text-emerald-500/70">${formatPriceCompact(pos.intended_tp)}</span>
        <span className="text-red-500/70">${formatPriceCompact(pos.intended_sl)}</span>
      </div>

      {/* PnL */}
      {hasPnl && (
        <span className={cn(
          "text-[11px] font-medium font-mono min-w-[50px] text-right",
          (pos.unrealized_pnl_pct ?? 0) >= 0 ? "text-emerald-500" : "text-red-500"
        )}>
          {(pos.unrealized_pnl_pct ?? 0) >= 0 ? "+" : ""}{pos.unrealized_pnl_pct?.toFixed(1)}%
        </span>
      )}

      {/* Size + age */}
      <div className="text-[10px] text-muted-foreground text-right min-w-[60px]">
        <div className="font-mono">${pos.quote_amount.toFixed(0)}</div>
        <div>{timeAgo(pos.created_at)}</div>
      </div>

      {/* Close button */}
      <button
        onClick={(e) => { e.stopPropagation(); onClose(pos.id); }}
        className="p-1 rounded hover:bg-red-500/10 text-muted-foreground hover:text-red-500 transition-colors"
        title="Close position"
      >
        <X size={12} />
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
          <div className="flex items-center gap-3 py-1.5 px-4 border-b border-border/20 text-[9px] font-bold text-muted-foreground uppercase tracking-wider">
            <span className="min-w-[70px]">Symbol</span>
            <span className="w-12">Status</span>
            <span className="flex-1">Entry / Now / TP / SL</span>
            <span className="min-w-[50px] text-right">PnL</span>
            <span className="min-w-[60px] text-right">Size / Age</span>
            <span className="w-6" />
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
