"use client";

import { useTradingPortfolio } from "@/hooks/useTradingData";
import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, DollarSign, Activity, Pause, Play } from "lucide-react";
import { useUpdateTradingConfig, usePauseTrading } from "@/hooks/useTradingData";

function StatCard({
  label,
  value,
  sub,
  positive,
  icon: Icon,
}: {
  label: string;
  value: string;
  sub?: string;
  positive?: boolean;
  icon?: React.ElementType;
}) {
  return (
    <div className="bg-card/60 backdrop-blur-md border border-border/40 rounded-xl p-4 flex flex-col gap-1">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-bold text-muted-foreground uppercase tracking-wider">{label}</span>
        {Icon && <Icon size={14} className="text-muted-foreground" />}
      </div>
      <span className={cn(
        "text-xl font-black tracking-tight",
        positive === true && "text-emerald-500",
        positive === false && "text-red-500",
      )}>{value}</span>
      {sub && <span className="text-[10px] text-muted-foreground">{sub}</span>}
    </div>
  );
}

export function PortfolioSummary() {
  const { data, isLoading, error } = useTradingPortfolio();
  const updateConfig = useUpdateTradingConfig();
  const pause = usePauseTrading();

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-card/60 border border-border/40 rounded-xl p-4 h-20 animate-pulse" />
        ))}
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-card/60 border border-border/40 rounded-xl p-4 text-center text-muted-foreground text-sm">
        Backend unavailable — start with <code className="text-xs bg-muted px-1 rounded">docker-compose up -d</code>
      </div>
    );
  }

  const pnlFromStart = data.balance - data.initial_capital;
  const pnlPct = (pnlFromStart / data.initial_capital) * 100;

  return (
    <div className="space-y-4">
      {/* Status bar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className={cn(
            "w-2 h-2 rounded-full",
            data.enabled ? "bg-emerald-500 animate-pulse" : "bg-muted-foreground"
          )} />
          <span className="text-sm font-bold">
            Paper Trading — {data.enabled ? "Active" : "Paused"}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {data.enabled ? (
            <button
              onClick={() => pause.mutate()}
              disabled={pause.isPending}
              className="flex items-center gap-1.5 text-[11px] font-bold px-3 py-1.5 rounded-lg bg-muted hover:bg-muted/80 text-muted-foreground hover:text-foreground transition-colors"
            >
              <Pause size={11} /> Pause
            </button>
          ) : (
            <button
              onClick={() => updateConfig.mutate({ enabled: true })}
              disabled={updateConfig.isPending}
              className="flex items-center gap-1.5 text-[11px] font-bold px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20 transition-colors"
            >
              <Play size={11} /> Enable
            </button>
          )}
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Balance"
          value={`$${data.balance.toFixed(2)}`}
          sub={`Started at $${data.initial_capital}`}
          icon={DollarSign}
        />
        <StatCard
          label="Total PnL"
          value={`${pnlFromStart >= 0 ? "+" : ""}$${pnlFromStart.toFixed(2)}`}
          sub={`${pnlPct >= 0 ? "+" : ""}${pnlPct.toFixed(1)}% from start`}
          positive={pnlFromStart >= 0}
          icon={pnlFromStart >= 0 ? TrendingUp : TrendingDown}
        />
        <StatCard
          label="Unrealized"
          value={`${data.unrealized_pnl >= 0 ? "+" : ""}$${data.unrealized_pnl.toFixed(2)}`}
          sub="Open positions MTM"
          positive={data.unrealized_pnl >= 0}
          icon={Activity}
        />
        <StatCard
          label="Exposure"
          value={`$${data.exposure.total_usdt.toFixed(0)}`}
          sub={
            data.exposure.open === 0 && data.exposure.pending > 0
              ? `${data.exposure.pct_of_balance.toFixed(0)}% potential • ${data.exposure.pending} pending`
              : data.exposure.pending > 0
              ? `${data.exposure.pct_of_balance.toFixed(0)}% of balance • ${data.exposure.open} open + ${data.exposure.pending} pending`
              : `${data.exposure.pct_of_balance.toFixed(0)}% of balance • ${data.exposure.open} open`
          }
        />
      </div>

      {/* Exposure bar */}
      {data.exposure.positions > 0 && (
        <div className="h-1.5 bg-muted rounded-full overflow-hidden">
          <div
            className="h-full bg-primary rounded-full transition-all duration-500"
            style={{ width: `${Math.min(data.exposure.pct_of_balance, 100)}%` }}
          />
        </div>
      )}
    </div>
  );
}
