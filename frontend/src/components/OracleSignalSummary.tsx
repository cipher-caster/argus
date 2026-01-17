"use client";

import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { useOracleSignalSummary } from "@/hooks/useAnalyticsData";
import { HelpCircle, Shield, TrendingUp, Zap } from "lucide-react";

export function OracleSignalSummary() {
  const { data, isLoading, error } = useOracleSignalSummary();

  if (isLoading) return <div className="h-[280px] flex items-center justify-center bg-secondary border border-border rounded-2xl animate-pulse text-muted-foreground font-bold uppercase tracking-widest text-xs">Scanning Market...</div>;
  if (error) return <div className="h-[280px] flex items-center justify-center bg-secondary border border-red-500/20 text-red-500 rounded-2xl italic text-xs">Oracle Insight Unavailable</div>;

  const confidence = Math.max(data?.bullish_pct || 0, data?.bearish_pct || 0);
  const marketState = data?.market_state || "Analyzing";

  return (
    <div className="bg-secondary border border-border rounded-2xl p-5 h-full relative overflow-hidden group hover:shadow-lg transition-all duration-300">
      {/* Subtle Background Icon */}
      <div className="absolute -top-6 -right-6 opacity-[0.03] group-hover:opacity-[0.07] transition-opacity duration-500 pointer-events-none">
        <Shield size={180} />
      </div>

      <div className="relative z-10 flex flex-col h-full">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-primary/10 flex items-center justify-center text-primary shadow-inner">
              <Zap size={20} fill="currentColor" />
            </div>
            <div>
              <h3 className="font-extrabold text-[15px] uppercase tracking-tight leading-none mb-1">Oracle Intelligence</h3>
              <p className="text-[10px] text-muted-foreground font-black uppercase tracking-widest leading-none">{marketState}</p>
            </div>
          </div>

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <button className="p-1 rounded-md text-muted-foreground hover:text-foreground transition-colors">
                  <HelpCircle size={14} />
                </button>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="max-w-[300px] p-4">
                <div className="space-y-3">
                  <div className="space-y-1">
                    <p className="text-[11px] font-black uppercase text-primary">AI Confidence</p>
                    <p className="text-[10px] text leading-relaxed">The highest momentum score detected across the market. Represents the strength and conviction of the current primary signals.</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-[11px] font-black uppercase text-foreground">Market Concentration</p>
                    <p className="text-[10px] text leading-relaxed">The percentage of Top 50 Perpetual symbols aligned in a specific direction (Price {">"} EMA200 + Momentum Score).</p>
                  </div>
                </div>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>

        {/* Main Content Grid */}
        <div className="flex-1 flex flex-col justify-between">
          <div className="space-y-6">
            {/* Confidence Metric */}
            <div>
              <div className="flex justify-between items-end mb-2">
                <span className="text-[11px] font-black text-muted-foreground uppercase tracking-wider">AI Confidence</span>
                <span className="text-2xl font-black text-foreground tracking-tighter leading-none">{confidence}%</span>
              </div>
              <div className="h-2 w-full bg-muted/50 rounded-full overflow-hidden flex ring-1 ring-border/50">
                <div className="h-full bg-primary transition-all duration-1000 ease-out shadow-[0_0_10px_rgba(var(--primary),0.5)]" style={{ width: `${confidence}%` }} />
              </div>
            </div>

            {/* Sentiment Concentration */}
            <div className="space-y-2">
              <div className="flex justify-between text-[10px] font-black uppercase tracking-widest">
                <span className="text-green-500">Bullish {data?.bullish_pct || 0}%</span>
                <span className="text-red-500">Bearish {data?.bearish_pct || 0}%</span>
              </div>
              <div className="h-1.5 w-full bg-muted/50 rounded-full overflow-hidden flex">
                <div className="h-full bg-green-500/80 transition-all duration-1000" style={{ width: `${data?.bullish_pct || 50}%` }} />
                <div className="h-full bg-red-500/80 transition-all duration-1000" style={{ width: `${data?.bearish_pct || 50}%` }} />
              </div>
            </div>

            {/* Alpha Signals Section */}
            <div className="pt-4 border-t border-border/50">
              <div className="flex items-center gap-2 mb-3 mt-1">
                <TrendingUp size={14} className="text-primary" />
                <span className="text-[11px] font-black uppercase tracking-widest text-foreground/80">Alpha Signals</span>
              </div>
              <div className="flex flex-wrap gap-2 min-h-[60px]">
                {data?.top_signals.map((sig: string) => (
                  <div key={sig} className="px-2.5 py-1.5 bg-background border border-border rounded-lg text-[10px] font-bold tracking-tight hover:border-primary/40 hover:bg-primary/5 transition-all cursor-default shadow-sm">
                    {sig}
                  </div>
                ))}
                {(!data?.top_signals || data.top_signals.length === 0) && <div className="text-[10px] text-muted-foreground italic font-medium py-1">No high-probability signals detected</div>}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
