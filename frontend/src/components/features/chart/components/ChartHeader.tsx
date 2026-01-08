"use client";

import { Dropdown } from "@/components/ui/Dropdown";
import { formatChange, formatPrice } from "@/lib/formatters";
import { cn } from "@/lib/utils";
import { IndicatorConfig, useIndicatorStore } from "@/stores/indicatorStore";
import { BarChart2, CandlestickChart as CandleIcon, ChevronDown, ChevronLeft, Edit2, Eye, EyeOff, Loader2, PlusCircle, RefreshCw, Search, Trash2, X } from "lucide-react";
import Link from "next/link";
import { TimeframeSelector } from "../TimeframeSelector";

interface ChartHeaderProps {
  symbol: string;
  price?: number;
  priceChangePercent?: number;
  isLoading?: boolean;
  isRefreshing?: boolean;
  timeframe?: string;
  onTimeframeChange?: (tf: string) => void;
  indicatorConfigs: IndicatorConfig[];
  onAddIndicator: () => void;
  onEditIndicator: (indicator: IndicatorConfig) => void;
  onOpenSettings?: () => void;
  onRefresh?: () => void;
  provider?: string;
}

export function ChartHeader({ symbol, price, priceChangePercent, isLoading, isRefreshing, timeframe, onTimeframeChange, indicatorConfigs, onAddIndicator, onEditIndicator, onOpenSettings, onRefresh, provider }: ChartHeaderProps) {
  const toggleVisibility = useIndicatorStore((s) => s.toggleVisibility);
  const removeIndicator = useIndicatorStore((s) => s.removeIndicator);

  const overlayIndicators = indicatorConfigs.filter((i) => i.visible && i.indicatorType === "overlay");

  return (
    <div className="flex items-center h-[38px] px-3 bg-secondary border-b border-border gap-1 select-none">
      <Link href="/" className="flex items-center justify-center text-muted-foreground w-8 h-8 rounded-md transition-all hover:text-foreground hover:bg-muted" title="Back to Markets">
        <ChevronLeft size={20} />
      </Link>

      {/* Brand / Home Link */}
      <Link href="/" className="flex items-center gap-2 no-underline px-1">
        <div className="w-2 h-2 bg-primary rounded-[2px] rotate-45" />
        <span className="font-extrabold text-[16px] text-foreground tracking-tighter">Argus</span>
      </Link>

      <div className="w-px h-5 bg-border mx-1" />

      {/* Symbol Section */}
      <div className="flex items-center gap-1 group">
        <Search size={16} className="text-muted-foreground cursor-pointer group-hover:text-foreground transition-colors" />
        <div className="flex items-center gap-3 ml-2">
          <span className="font-bold text-[14px] text-foreground mr-2">{symbol}</span>
          {price !== undefined && (
            <div className="flex items-center gap-2 pl-3 border-l border-border">
              <span className="font-bold text-[14px] text-foreground">${formatPrice(price)}</span>
              <span className={cn("text-[12px] font-semibold", priceChangePercent !== undefined && priceChangePercent >= 0 ? "text-success" : "text-danger")}>{formatChange(priceChangePercent)}</span>
            </div>
          )}
        </div>
      </div>

      <div className="w-px h-5 bg-border mx-1" />

      {/* Comparison */}
      <button
        className="w-6 h-6 rounded-full border border-border bg-transparent text-muted-foreground flex items-center justify-center cursor-pointer transition-all hover:text-foreground hover:border-muted-foreground hover:bg-muted"
        title="Compare or Add Symbol"
      >
        <PlusCircle size={18} />
      </button>

      <div className="w-px h-5 bg-border mx-1" />

      {/* Timeframes */}
      <div className="flex items-center gap-1">{timeframe && onTimeframeChange && <TimeframeSelector selected={timeframe} onChange={onTimeframeChange} />}</div>

      <div className="w-px h-5 bg-border mx-1" />

      {/* Chart Type */}
      <div className="flex items-center">
        <button className="w-7 h-7 border-none bg-transparent text-muted-foreground flex items-center justify-center cursor-pointer rounded-md hover:text-foreground hover:bg-muted" title="Chart Style">
          <CandleIcon size={20} />
        </button>
      </div>

      <div className="w-px h-5 bg-border mx-1" />

      {/* Indicators */}
      <div className="flex items-center gap-1">
        <div className="flex items-center bg-transparent rounded-md overflow-hidden group/btn-group">
          <button className="h-7 px-1.5 border-none bg-transparent text-muted-foreground flex items-center gap-1 cursor-pointer font-semibold text-[13px] hover:text-foreground group-hover/btn-group:bg-muted" onClick={onAddIndicator}>
            <BarChart2 size={18} />
            <span>Indicators</span>
          </button>
          <Dropdown
            trigger={
              <button className="h-7 px-0.5 border-none bg-transparent text-muted-foreground cursor-pointer flex items-center hover:text-foreground hover:bg-black/5 group-hover/btn-group:bg-muted">
                <ChevronDown size={14} />
              </button>
            }
          >
            <div className="min-width-[220px] py-1">
              <div className="px-3 py-2 text-[11px] font-bold text-muted-foreground uppercase tracking-wider">Active Indicators</div>
              {indicatorConfigs.length === 0 ? (
                <div className="p-3 text-[12px] text-muted-foreground text-center">No indicators added</div>
              ) : (
                indicatorConfigs.map((ind) => (
                  <div key={ind.id} className="flex items-center justify-between px-3 py-1.5 hover:bg-muted transition-colors">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full" style={{ background: ind.color }}></div>
                      <span className="text-[13px] text-foreground">{ind.displayName}</span>
                    </div>
                    <div className="flex gap-1">
                      <button
                        className="bg-transparent border-none p-1 cursor-pointer text-muted-foreground rounded-md flex items-center hover:text-foreground hover:bg-black/5"
                        onClick={() => toggleVisibility(ind.id)}
                        title={ind.visible ? "Hide Indicator" : "Show Indicator"}
                      >
                        {ind.visible ? <Eye size={14} /> : <EyeOff size={14} />}
                      </button>
                      <button className="bg-transparent border-none p-1 cursor-pointer text-muted-foreground rounded-md flex items-center hover:text-foreground hover:bg-black/5" onClick={() => onEditIndicator(ind)} title="Edit Indicator">
                        <Edit2 size={14} />
                      </button>
                      <button className="bg-transparent border-none p-1 cursor-pointer text-muted-foreground rounded-md flex items-center hover:text-danger hover:bg-black/5" onClick={() => removeIndicator(ind.id)} title="Remove Indicator">
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </Dropdown>
        </div>

        {overlayIndicators.length > 0 && (
          <div className="flex gap-1 ml-2">
            {overlayIndicators.map((i) => (
              <span
                key={i.id}
                className="px-1.5 py-[1px] text-[9px] font-bold border border-current rounded-[2px] bg-transparent cursor-pointer inline-flex items-center gap-1 hover:bg-muted transition-colors"
                style={{ color: i.color }}
                onClick={() => onEditIndicator(i)}
              >
                {i.displayName}
                <button
                  className="flex items-center justify-center bg-transparent border-none text-current opacity-60 cursor-pointer p-0 w-3.5 h-3.5 rounded-full hover:opacity-100 hover:bg-black/10"
                  onClick={(e) => {
                    e.stopPropagation();
                    removeIndicator(i.id);
                  }}
                  title="Remove Indicator"
                >
                  <X size={10} />
                </button>
              </span>
            ))}
          </div>
        )}
      </div>

      {isLoading && <Loader2 size={16} className="ml-auto animate-spin text-primary" />}

      <div className="ml-auto flex items-center gap-3">
        {provider && <span className="text-[10px] font-bold text-muted-foreground bg-muted px-1.5 py-[2px] rounded-[4px] border border-border tracking-wider uppercase">{provider}</span>}
        {onRefresh && (
          <button
            className={cn("w-7 h-7 border-none bg-transparent text-muted-foreground flex items-center justify-center cursor-pointer rounded-md hover:text-foreground hover:bg-muted transition-colors", isRefreshing && "animate-spin")}
            onClick={onRefresh}
            title="Refresh Chart Data"
            disabled={isRefreshing}
          >
            <RefreshCw size={16} />
          </button>
        )}
        {onOpenSettings && (
          <button className="w-7 h-7 border-none bg-transparent text-muted-foreground flex items-center justify-center cursor-pointer rounded-md hover:text-foreground hover:bg-muted transition-colors" onClick={onOpenSettings} title="Chart Settings">
            <Edit2 size={16} />
          </button>
        )}
      </div>
    </div>
  );
}
