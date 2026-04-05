"use client";

import { useTradingPortfolio, useTradingStats } from "@/hooks/useTradingData";
import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, DollarSign, ChevronRight } from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import Link from "next/link";

export function TradingWidget() {
  const { data: portfolio } = useTradingPortfolio();
  const { data: stats } = useTradingStats();

  // Don't render if backend isn't available or trading never started
  if (!portfolio) return null;

  const pnlFromStart = portfolio.balance - portfolio.initial_capital;
  const pnlPct = (pnlFromStart / portfolio.initial_capital) * 100;
  const isPositive = pnlFromStart >= 0;

  return (
    <div className="bg-secondary/30 border border-border/50 rounded-2xl overflow-hidden w-full">
      <div className="flex items-center justify-between px-4 py-3 border-b border-border/30">
        <div className="flex items-center gap-2">
          <DollarSign size={14} className="text-primary" />
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <h3 className="text-sm font-black tracking-tight cursor-help">Paper Trading</h3>
              </TooltipTrigger>
              <TooltipContent side="bottom" align="start" className="max-w-[240px] text-xs">
                Simulated portfolio tracking signal performance — balance, P&L, win rate, and open positions
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          <div className={cn(
            "w-1.5 h-1.5 rounded-full",
            portfolio.enabled ? "bg-emerald-500 animate-pulse" : "bg-muted-foreground"
          )} />
        </div>
        <div className="flex items-center gap-2">
          {portfolio.enabled ? (
            <span className="text-[10px] font-bold text-emerald-500">ACTIVE</span>
          ) : (
            <span className="text-[10px] font-bold text-muted-foreground">PAUSED</span>
          )}
          <Link
            href="/trading"
            className="flex items-center gap-1 text-[10px] text-muted-foreground hover:text-foreground transition-colors font-bold"
          >
            Trading <ChevronRight size={10} />
          </Link>
        </div>
      </div>

      <div className="px-4 py-3 flex items-center justify-between">
        {/* Balance */}
        <div>
          <div className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider">Balance</div>
          <div className="text-lg font-black">${portfolio.balance.toFixed(2)}</div>
          <div className={cn(
            "text-[11px] font-bold",
            isPositive ? "text-emerald-500" : "text-red-500"
          )}>
            {pnlFromStart >= 0 ? "+" : ""}${pnlFromStart.toFixed(2)} ({pnlPct >= 0 ? "+" : ""}{pnlPct.toFixed(1)}%)
          </div>
        </div>

        {/* Stats */}
        <div className="flex items-center gap-4 text-right">
          {stats && stats.total_trades > 0 && (
            <>
              <div>
                <div className="text-[10px] text-muted-foreground font-bold">Win Rate</div>
                <div className={cn(
                  "text-[14px] font-black",
                  (stats.win_rate ?? 0) >= 50 ? "text-emerald-500" : "text-red-500"
                )}>
                  {stats.win_rate !== null ? `${stats.win_rate}%` : "—"}
                </div>
              </div>
              <div>
                <div className="text-[10px] text-muted-foreground font-bold">Trades</div>
                <div className="text-[14px] font-black">{stats.total_trades}</div>
              </div>
            </>
          )}

          {portfolio.exposure.positions > 0 && (
            <div>
              <div className="text-[10px] text-muted-foreground font-bold">Pending</div>
              <div className="text-[14px] font-black text-primary">{portfolio.exposure.positions}</div>
            </div>
          )}
        </div>
      </div>

      {/* Unrealized PnL bar */}
      {portfolio.unrealized_pnl !== 0 && (
        <div className={cn(
          "px-4 py-2 border-t border-border/20 text-[10px] font-bold flex items-center gap-1.5",
          portfolio.unrealized_pnl >= 0 ? "text-emerald-500" : "text-red-500"
        )}>
          {portfolio.unrealized_pnl >= 0 ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
          Unrealized: {portfolio.unrealized_pnl >= 0 ? "+" : ""}${portfolio.unrealized_pnl.toFixed(2)}
        </div>
      )}
    </div>
  );
}
