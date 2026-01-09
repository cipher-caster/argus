"use client";

import { useStrategyOracle } from "@/hooks/useStrategyOracle";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Info, TrendingUp, TrendingDown, Minus, ShieldAlert, Zap, Target } from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

interface StrategyOraclePanelProps {
  symbol: string;
  timeframe: string;
}

export function StrategyOraclePanel({ symbol, timeframe }: StrategyOraclePanelProps) {
  const { data, isLoading, error } = useStrategyOracle(symbol, timeframe);

  if (isLoading) {
    return (
      <Card className="absolute top-4 right-4 z-20 w-64 p-4 bg-background/80 backdrop-blur-md border-border/50 shadow-xl animate-pulse">
        <div className="h-4 bg-muted rounded w-1/2 mb-4" />
        <div className="space-y-2">
          <div className="h-8 bg-muted rounded" />
          <div className="h-8 bg-muted rounded" />
        </div>
      </Card>
    );
  }

  if (error || !data) return null;

  const isBullish = data.bias === "BULLISH";
  const isBearish = data.bias === "BEARISH";
  
  const getSignalColor = (signal: string) => {
    if (signal.includes("BUY")) return "text-emerald-700 dark:text-emerald-400 bg-emerald-500/10 border-emerald-500/20";
    if (signal.includes("SELL")) return "text-rose-700 dark:text-rose-400 bg-rose-500/10 border-rose-500/20";
    return "text-slate-600 dark:text-slate-400 bg-slate-400/10 border-slate-400/20";
  };

  const getVoterIcon = (val: number) => {
    if (val > 0) return <TrendingUp className="w-3 h-3 text-emerald-600 dark:text-emerald-500" />;
    if (val < 0) return <TrendingDown className="w-3 h-3 text-rose-600 dark:text-rose-500" />;
    return <Minus className="w-3 h-3 text-slate-600 dark:text-slate-500" />;
  };

  return (
    <Card className="absolute top-4 right-4 z-20 w-64 p-0 bg-background/95 backdrop-blur-md border-border shadow-2xl overflow-hidden select-none">
      {/* Header */}
      <div className="bg-muted p-3 border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-amber-600 dark:text-amber-500" />
          <span className="font-bold text-xs tracking-wider uppercase text-foreground">Argus Oracle</span>
        </div>
        <Badge variant="outline" className="text-[10px] h-5 px-1.5 font-mono opacity-80 border-muted-foreground/30 text-foreground">
          V9.0
        </Badge>
      </div>

      <div className="p-4 space-y-4">
        {/* Signal & Confidence */}
        <div className="flex flex-col gap-1">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground dark:text-muted-foreground uppercase tracking-tighter font-bold">Signal</span>
            <Badge className={cn("text-xs font-bold px-2 border", getSignalColor(data.signal))}>
              {data.signal.replace("_", " ")}
            </Badge>
          </div>
          <div className="flex items-center justify-between mt-2">
            <span className="text-xs text-muted-foreground dark:text-muted-foreground uppercase tracking-tighter font-bold">Confidence</span>
            <span className="text-sm font-mono font-bold text-foreground">{data.confidence}</span>
          </div>
        </div>

        {/* Macro Bias */}
        <div className="p-2.5 rounded-lg bg-muted/50 border border-border space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <Info className="w-3.5 h-3.5 text-muted-foreground" />
              <span className="text-[11px] font-bold text-muted-foreground uppercase">Macro Trend (1D)</span>
            </div>
            <span className={cn(
              "text-[11px] font-bold",
              isBullish ? "text-emerald-700 dark:text-emerald-500" : isBearish ? "text-rose-700 dark:text-rose-500" : "text-slate-600 dark:text-slate-500"
            )}>
              {data.bias}
            </span>
          </div>
          
          {/* Macro Detail Grid */}
          <div className="grid grid-cols-3 gap-1">
             {Object.entries(data.macro.details).map(([key, val]) => (
               <div key={key} className="flex flex-col items-center p-1 rounded bg-background border border-border/50">
                 <span className="text-[9px] uppercase font-bold opacity-70 text-foreground mb-0.5">{key}</span>
                 {val ? <TrendingUp className="w-2.5 h-2.5 text-emerald-600 dark:text-emerald-500" /> : <TrendingDown className="w-2.5 h-2.5 text-rose-600 dark:text-rose-500" />}
               </div>
             ))}
          </div>
        </div>

        {/* Advice */}
        <div className="p-3 rounded-lg bg-amber-500/10 dark:bg-amber-500/5 border border-amber-500/30 dark:border-amber-500/20">
          <div className="flex gap-2">
            <ShieldAlert className="w-4 h-4 text-amber-600 dark:text-amber-500 shrink-0" />
            <p className="text-[11px] leading-relaxed text-amber-900 dark:text-amber-200/90 font-bold italic">
              "{data.advice}"
            </p>
          </div>
        </div>

        {/* Targets (if any) */}
        {data.targets.tp1 > 0 && (
          <div className="pt-2 border-t border-border space-y-2">
            <div className="flex items-center gap-1.5 mb-2">
              <Target className="w-3.5 h-3.5 text-blue-600 dark:text-blue-500" />
              <span className="text-[11px] font-bold text-muted-foreground uppercase">Levels</span>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-emerald-700 dark:text-emerald-400 font-medium">Target 1</span>
              <span className="font-mono font-bold text-foreground">{data.targets.tp1.toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-rose-700 dark:text-rose-400 font-medium">Stop Loss</span>
              <span className="font-mono font-bold text-foreground">{data.targets.sl.toLocaleString()}</span>
            </div>
          </div>
        )}
      </div>

      {/* Footer / Meta */}
      <div className="bg-muted p-2 border-t border-border flex justify-between items-center px-4">
        <div className="flex items-center gap-1">
          <div className={cn("w-1.5 h-1.5 rounded-full animate-pulse", 
            data.volatility === "DANGER" ? "bg-rose-600 dark:bg-rose-500" : "bg-emerald-600 dark:bg-emerald-500"
          )} />
          <span className="text-[10px] font-bold text-muted-foreground uppercase">{data.volatility} VOL</span>
        </div>
        <span className="text-[10px] text-muted-foreground font-bold font-mono uppercase">{data.state}</span>
      </div>
    </Card>
  );
}
