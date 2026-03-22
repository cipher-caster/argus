"use client";

import { Position } from "@/lib/api";
import { cn } from "@/lib/utils";
import { X, Target, DollarSign, Layers, Clock, BarChart2 } from "lucide-react";
import { useEffect } from "react";
import { createPortal } from "react-dom";

interface TradeDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  position: Position | null;
}

/* ── Helpers ─────────────────────────────────────────────── */

function formatPrice(p: number) {
  if (p >= 1000) return p.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  if (p >= 1) return p.toFixed(4);
  return p.toFixed(6);
}

function formatDateTime(ms: number) {
  const d = new Date(ms);
  const mon = d.toLocaleString("en-US", { month: "short" });
  const day = d.getDate();
  const yr = d.getFullYear();
  const hh = d.getHours().toString().padStart(2, "0");
  const mm = d.getMinutes().toString().padStart(2, "0");
  return `${mon} ${day}, ${yr} ${hh}:${mm}`;
}

function duration(from: number | null, to: number | null): string {
  if (!from || !to) return "\u2014";
  const ms = to - from;
  const h = Math.floor(ms / 3_600_000);
  const d = Math.floor(ms / 86_400_000);
  if (d >= 1) return `${d}d ${h % 24}h`;
  if (h >= 1) return `${h}h`;
  return "< 1h";
}

/* ── Tiny sub-components ─────────────────────────────────── */

function Label({ children }: { children: React.ReactNode }) {
  return <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">{children}</span>;
}

function Value({ children, className }: { children: React.ReactNode; className?: string }) {
  return <span className={cn("text-xs font-mono font-medium", className)}>{children}</span>;
}

function SectionHeader({ icon: Icon, title }: { icon: React.ElementType; title: string }) {
  return (
    <div className="flex items-center gap-1.5 mb-2">
      <Icon size={12} className="text-muted-foreground" />
      <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">{title}</span>
    </div>
  );
}

function InfoCard({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn("bg-muted/30 border border-border/50 rounded-lg p-2", className)}>{children}</div>;
}

/* ── Modal ───────────────────────────────────────────────── */

export function TradeDetailModal({ isOpen, onClose, position }: TradeDetailModalProps) {
  // Escape key handler
  useEffect(() => {
    if (!isOpen) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [isOpen, onClose]);

  if (!isOpen || !position) return null;

  const pos = position;
  const base = pos.symbol.replace("USDT", "");
  const isLong = pos.direction === "LONG";
  const entry = pos.actual_entry ?? pos.intended_entry;
  const isClosed = pos.status === "CLOSED";
  const isOpen_ = pos.status === "OPEN";

  // Price distances
  const tpDist = ((pos.intended_tp - entry) / entry) * 100;
  const slDist = ((pos.intended_sl - entry) / entry) * 100;
  const rrRatio = Math.abs(tpDist / slDist);

  // Extended position type that may have market_state_at_close
  const marketStateAtClose = (pos as Position & { market_state_at_close?: string | null }).market_state_at_close;

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      onClick={onClose}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      {/* Card */}
      <div
        className="relative z-10 w-full max-w-lg max-h-[85vh] overflow-y-auto bg-card border border-border/60 rounded-2xl shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* ── Header ─────────────────────────────────────── */}
        <div className="sticky top-0 z-10 flex items-center justify-between px-4 py-3 border-b border-border/40 bg-muted/50 backdrop-blur-md rounded-t-2xl">
          <div className="flex items-center gap-2">
            <span className="text-sm font-black tracking-tight">{base}</span>
            <span className={cn(
              "text-[9px] font-black px-1.5 py-0.5 rounded uppercase tracking-wide",
              isLong ? "bg-emerald-500/10 text-emerald-500" : "bg-red-500/10 text-red-500"
            )}>
              {pos.direction}
            </span>
            <span className={cn(
              "text-[9px] font-black px-1.5 py-0.5 rounded uppercase tracking-wide",
              pos.status === "OPEN" && "bg-emerald-500/10 text-emerald-500",
              pos.status === "PENDING" && "bg-yellow-500/10 text-yellow-500",
              pos.status === "CLOSED" && "bg-muted-foreground/10 text-muted-foreground",
              pos.status === "CANCELLED" && "bg-muted-foreground/10 text-muted-foreground",
            )}>
              {pos.status}
            </span>
            {pos.outcome && (
              <span className={cn(
                "text-[9px] font-black px-1.5 py-0.5 rounded",
                pos.outcome === "WIN" && "bg-emerald-500/10 text-emerald-500",
                pos.outcome === "LOSS" && "bg-red-500/10 text-red-500",
                pos.outcome === "EXPIRED" && "bg-muted-foreground/10 text-muted-foreground",
              )}>
                {pos.outcome === "WIN" ? "WIN" : pos.outcome === "LOSS" ? "LOSS" : "EXPIRED"}
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-secondary/60 text-muted-foreground hover:text-foreground transition-colors"
          >
            <X size={16} />
          </button>
        </div>

        <div className="divide-y divide-border/30">
          {/* ── Price Levels ───────────────────────────────── */}
          <div className="px-4 py-3">
            <SectionHeader icon={Target} title="Price Levels" />
            <div className="grid grid-cols-3 gap-2">
              <InfoCard>
                <Label>Intended Entry</Label>
                <div><Value>${formatPrice(pos.intended_entry)}</Value></div>
              </InfoCard>
              <InfoCard>
                <Label>Actual Entry</Label>
                <div><Value>{pos.actual_entry ? `$${formatPrice(pos.actual_entry)}` : "Pending"}</Value></div>
              </InfoCard>
              <InfoCard>
                <Label>Actual Exit</Label>
                <div><Value>{pos.actual_exit ? `$${formatPrice(pos.actual_exit)}` : "\u2014"}</Value></div>
              </InfoCard>
              <InfoCard>
                <Label>Take Profit</Label>
                <div>
                  <Value className="text-emerald-500">${formatPrice(pos.intended_tp)}</Value>
                  <span className="text-[10px] text-emerald-500/60 ml-1">
                    {tpDist >= 0 ? "+" : ""}{tpDist.toFixed(2)}%
                  </span>
                </div>
              </InfoCard>
              <InfoCard>
                <Label>Stop Loss</Label>
                <div>
                  <Value className="text-red-500">${formatPrice(pos.intended_sl)}</Value>
                  <span className="text-[10px] text-red-500/60 ml-1">
                    {slDist.toFixed(2)}%
                  </span>
                </div>
              </InfoCard>
              <InfoCard>
                <Label>R:R Ratio</Label>
                <div><Value>{rrRatio.toFixed(2)}</Value></div>
              </InfoCard>
            </div>
            {pos.current_price !== undefined && (
              <InfoCard className="mt-2">
                <Label>Current Price</Label>
                <div><Value>${formatPrice(pos.current_price)}</Value></div>
              </InfoCard>
            )}
          </div>

          {/* ── P&L ────────────────────────────────────────── */}
          {(isClosed || (isOpen_ && pos.unrealized_pnl_usd !== undefined)) && (
            <div className="px-4 py-3">
              <SectionHeader icon={DollarSign} title="Profit & Loss" />
              {isClosed && pos.pnl_usd !== null && pos.pnl_pct !== null ? (
                <InfoCard className={cn(
                  "border",
                  pos.outcome === "WIN" ? "border-emerald-500/30 bg-emerald-500/5" : "border-red-500/30 bg-red-500/5"
                )}>
                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Realized PnL</Label>
                      <div className={cn(
                        "text-lg font-medium font-mono",
                        pos.pnl_usd >= 0 ? "text-emerald-500" : "text-red-500"
                      )}>
                        {pos.pnl_usd >= 0 ? "+" : ""}{pos.pnl_usd.toFixed(2)} USDT
                      </div>
                    </div>
                    <div className={cn(
                      "text-xl font-medium font-mono",
                      pos.pnl_pct >= 0 ? "text-emerald-500" : "text-red-500"
                    )}>
                      {pos.pnl_pct >= 0 ? "+" : ""}{pos.pnl_pct.toFixed(2)}%
                    </div>
                  </div>
                </InfoCard>
              ) : isOpen_ && pos.unrealized_pnl_usd !== undefined && pos.unrealized_pnl_pct !== undefined ? (
                <InfoCard className={cn(
                  "border",
                  pos.unrealized_pnl_usd >= 0 ? "border-emerald-500/30 bg-emerald-500/5" : "border-red-500/30 bg-red-500/5"
                )}>
                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Unrealized PnL</Label>
                      <div className={cn(
                        "text-lg font-medium font-mono",
                        pos.unrealized_pnl_usd >= 0 ? "text-emerald-500" : "text-red-500"
                      )}>
                        {pos.unrealized_pnl_usd >= 0 ? "+" : ""}{pos.unrealized_pnl_usd.toFixed(2)} USDT
                      </div>
                    </div>
                    <div className={cn(
                      "text-xl font-medium font-mono",
                      pos.unrealized_pnl_pct >= 0 ? "text-emerald-500" : "text-red-500"
                    )}>
                      {pos.unrealized_pnl_pct >= 0 ? "+" : ""}{pos.unrealized_pnl_pct.toFixed(2)}%
                    </div>
                  </div>
                </InfoCard>
              ) : null}
            </div>
          )}

          {/* ── Position Sizing ────────────────────────────── */}
          <div className="px-4 py-3">
            <SectionHeader icon={Layers} title="Position Sizing" />
            <div className="grid grid-cols-3 gap-2">
              <InfoCard>
                <Label>Quantity</Label>
                <div><Value>{Number(pos.quantity.toFixed(8))}</Value></div>
              </InfoCard>
              <InfoCard>
                <Label>Quote Amount</Label>
                <div><Value>${pos.quote_amount.toFixed(2)}</Value></div>
              </InfoCard>
              <InfoCard>
                <Label>Risk Amount</Label>
                <div><Value>${pos.risk_amount.toFixed(2)}</Value></div>
              </InfoCard>
            </div>
            <InfoCard className="mt-2">
              <div className="flex items-center justify-between mb-1">
                <Label>Conviction</Label>
                <Value>{pos.conviction}/100</Value>
              </div>
              <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                <div
                  className={cn(
                    "h-full rounded-full transition-all",
                    pos.conviction >= 70 ? "bg-emerald-500" : pos.conviction >= 40 ? "bg-amber-500" : "bg-red-500"
                  )}
                  style={{ width: `${pos.conviction}%` }}
                />
              </div>
            </InfoCard>
          </div>

          {/* ── Timing ─────────────────────────────────────── */}
          <div className="px-4 py-3">
            <SectionHeader icon={Clock} title="Timing" />
            <div className="grid grid-cols-2 gap-2">
              <InfoCard>
                <Label>Created</Label>
                <div><Value>{formatDateTime(pos.created_at)}</Value></div>
              </InfoCard>
              <InfoCard>
                <Label>Filled</Label>
                <div><Value>{pos.filled_at ? formatDateTime(pos.filled_at) : "Not filled"}</Value></div>
              </InfoCard>
              <InfoCard>
                <Label>Closed</Label>
                <div><Value>{pos.closed_at ? formatDateTime(pos.closed_at) : "Still active"}</Value></div>
              </InfoCard>
              <InfoCard>
                <Label>Duration</Label>
                <div><Value>{duration(pos.created_at, pos.closed_at ?? Date.now())}</Value></div>
              </InfoCard>
            </div>
            <InfoCard className="mt-2">
              <Label>Fill Time</Label>
              <div><Value>{duration(pos.created_at, pos.filled_at)}</Value></div>
            </InfoCard>
          </div>

          {/* ── Context ────────────────────────────────────── */}
          <div className="px-4 py-3">
            <SectionHeader icon={BarChart2} title="Context" />
            <div className="grid grid-cols-2 gap-2">
              <InfoCard>
                <Label>Market State (Open)</Label>
                <div><Value>{pos.market_state}</Value></div>
              </InfoCard>
              <InfoCard>
                <Label>Market State (Close)</Label>
                <div><Value>{marketStateAtClose ?? "\u2014"}</Value></div>
              </InfoCard>
            </div>
            <InfoCard className="mt-2">
              <Label>Fired Reason</Label>
              <div className="mt-0.5"><Value>{pos.fired_reason}</Value></div>
            </InfoCard>
            <InfoCard className="mt-2">
              <Label>Signal Link</Label>
              <div>
                <Value>
                  {pos.signal_log_id ? `Signal #${pos.signal_log_id}` : "No linked signal"}
                </Value>
              </div>
            </InfoCard>
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
}
