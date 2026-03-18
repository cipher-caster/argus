"use client";

import { useTradingConfig, useUpdateTradingConfig } from "@/hooks/useTradingData";
import { TradingConfig } from "@/lib/api";
import { useState, useEffect } from "react";
import { Settings2, Save } from "lucide-react";
import { cn } from "@/lib/utils";

function Field({
  label,
  name,
  value,
  onChange,
  type = "number",
  step,
  min,
  max,
  hint,
}: {
  label: string;
  name: keyof TradingConfig;
  value: string | number | boolean;
  onChange: (key: keyof TradingConfig, val: string | number | boolean) => void;
  type?: "number" | "toggle";
  step?: number;
  min?: number;
  max?: number;
  hint?: string;
}) {
  if (type === "toggle") {
    return (
      <div className="flex items-center justify-between py-2.5 border-b border-border/20 last:border-0">
        <div>
          <div className="text-[12px] font-bold">{label}</div>
          {hint && <div className="text-[10px] text-muted-foreground">{hint}</div>}
        </div>
        <button
          type="button"
          onClick={() => onChange(name, !value)}
          className={cn(
            "w-10 h-5 rounded-full relative transition-colors",
            value ? "bg-emerald-500" : "bg-muted"
          )}
        >
          <span className={cn(
            "absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform",
            value ? "translate-x-5" : "translate-x-0.5"
          )} />
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-between py-2.5 border-b border-border/20 last:border-0">
      <div>
        <div className="text-[12px] font-bold">{label}</div>
        {hint && <div className="text-[10px] text-muted-foreground">{hint}</div>}
      </div>
      <input
        type="number"
        value={value as number}
        step={step ?? 1}
        min={min}
        max={max}
        onChange={(e) => onChange(name, parseFloat(e.target.value))}
        className="w-20 text-right text-[12px] font-mono bg-muted border border-border rounded-lg px-2 py-1 outline-none focus:border-primary"
      />
    </div>
  );
}

export function TradingConfigPanel() {
  const { data: config, isLoading } = useTradingConfig();
  const update = useUpdateTradingConfig();
  const [local, setLocal] = useState<Partial<TradingConfig>>({});
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    if (config) setLocal(config);
  }, [config]);

  function handleChange(key: keyof TradingConfig, val: string | number | boolean) {
    setLocal(prev => ({ ...prev, [key]: val }));
    setDirty(true);
  }

  function handleSave() {
    const { correlation_groups, ...patch } = local as TradingConfig;
    update.mutate(patch, {
      onSuccess: () => setDirty(false),
    });
  }

  if (isLoading || !local.initial_capital) {
    return <div className="h-32 flex items-center justify-center text-muted-foreground text-xs">Loading config...</div>;
  }

  return (
    <div className="bg-card/60 backdrop-blur-md rounded-2xl border border-border/40 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-border/30">
        <div className="flex items-center gap-2">
          <Settings2 size={14} className="text-primary" />
          <h3 className="text-sm font-black tracking-tight">Risk Settings</h3>
        </div>
        {dirty && (
          <button
            onClick={handleSave}
            disabled={update.isPending}
            className="flex items-center gap-1.5 text-[11px] font-bold px-3 py-1.5 rounded-lg bg-primary/10 text-primary hover:bg-primary/20 transition-colors"
          >
            <Save size={11} /> {update.isPending ? "Saving..." : "Save"}
          </button>
        )}
      </div>
      <div className="px-4 py-2">
        <Field label="Initial Capital ($)" name="initial_capital" value={local.initial_capital ?? 100} onChange={handleChange} min={10} step={10} hint="Starting portfolio size in USDT" />
        <Field label="Risk Per Trade (%)" name="max_position_size_pct" value={local.max_position_size_pct ?? 10} onChange={handleChange} min={1} max={25} step={0.5} hint="% of balance risked on each trade" />
        <Field label="Max Positions" name="max_concurrent_positions" value={local.max_concurrent_positions ?? 3} onChange={handleChange} min={1} max={10} hint="Max simultaneous open + pending" />
        <Field label="Max Correlated" name="max_correlated_positions" value={local.max_correlated_positions ?? 2} onChange={handleChange} min={1} max={5} hint="Max BTC-correlated coins at once" />
        <Field label="Max Drawdown (%)" name="max_drawdown_pct" value={local.max_drawdown_pct ?? 15} onChange={handleChange} min={5} max={50} step={1} hint="Circuit breaker threshold" />
        <Field label="Min Conviction" name="min_conviction" value={local.min_conviction ?? 65} onChange={handleChange} min={0} max={100} hint="Minimum signal conviction score" />
        <Field label="Order Expiry (hours)" name="order_expiry_hours" value={local.order_expiry_hours ?? 8} onChange={handleChange} min={1} max={48} hint="Cancel unfilled PENDING orders after this" />
      </div>
    </div>
  );
}
