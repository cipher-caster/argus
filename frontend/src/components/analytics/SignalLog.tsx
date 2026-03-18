"use client";

import { useState, useEffect } from "react";
import { useSignalLog, useSignalLogConfig, useUpdateSignalLogConfig } from "@/hooks/useAnalyticsData";
import { SignalLogItem, SignalLogConfig } from "@/lib/api";
import { cn } from "@/lib/utils";
import { RefreshCw, Settings2, Save, Check } from "lucide-react";

const SYMBOLS = ["All", "BTC", "ETH", "BNB", "TRX", "XRP", "FET", "NEAR", "ARB", "ATOM", "DOGE", "APT"];
const SOURCES = ["All", "Live", "Backtest"];

const OUTCOME_CONFIG = {
  WIN:    { label: "WIN",    emoji: "✅", cls: "text-emerald-500 dark:text-emerald-400 bg-emerald-500/10" },
  LOSS:   { label: "LOSS",   emoji: "❌", cls: "text-red-500 dark:text-red-400 bg-red-500/10" },
  REVIEW: { label: "REVIEW", emoji: "👀", cls: "text-amber-500 dark:text-amber-400 bg-amber-500/10" },
  OPEN:   { label: "OPEN",   emoji: "🔄", cls: "text-sky-500 dark:text-sky-400 bg-sky-500/10" },
} as const;

function formatPrice(p: number) {
  if (p >= 1000) return p.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  if (p >= 1) return p.toFixed(4);
  return p.toFixed(6);
}

function timeAgo(ms: number) {
  const diff = Date.now() - ms;
  const h = Math.floor(diff / 3_600_000);
  const d = Math.floor(diff / 86_400_000);
  if (d >= 1) return `${d}d ago`;
  if (h >= 1) return `${h}h ago`;
  return "< 1h ago";
}

function pct(from: number, to: number, dir: "LONG" | "SHORT") {
  const raw = dir === "LONG" ? ((to - from) / from) * 100 : ((from - to) / from) * 100;
  return (raw >= 0 ? "+" : "") + raw.toFixed(1) + "%";
}

function SignalRow({ item }: { item: SignalLogItem }) {
  const cfg = OUTCOME_CONFIG[item.outcome] ?? OUTCOME_CONFIG.OPEN;
  const isLong = item.direction === "LONG";
  const base = item.symbol.replace("USDT", "");

  return (
    <tr className="border-b border-border/30 hover:bg-secondary/20 transition-colors text-[12px]">
      <td className="py-3 px-4 font-black tracking-tight">
        <span className={cn("font-bold", isLong ? "text-emerald-500 dark:text-emerald-400" : "text-red-500 dark:text-red-400")}>
          {base}
        </span>
        <span className={cn(
          "ml-2 text-[10px] font-black px-1.5 py-0.5 rounded",
          isLong ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400" : "bg-red-500/10 text-red-600 dark:text-red-400"
        )}>
          {item.direction}
        </span>
      </td>
      <td className="py-3 px-4 font-mono text-muted-foreground">${formatPrice(item.entry)}</td>
      <td className="py-3 px-4 font-mono text-emerald-600 dark:text-emerald-400">
        ${formatPrice(item.tp)}
        <span className="ml-1 text-[10px] opacity-60">{pct(item.entry, item.tp, item.direction)}</span>
      </td>
      <td className="py-3 px-4 font-mono text-red-600 dark:text-red-400">
        ${formatPrice(item.sl)}
        <span className="ml-1 text-[10px] opacity-60">{pct(item.entry, item.sl, item.direction)}</span>
      </td>
      <td className="py-3 px-4">
        <div className="flex items-center gap-1">
          <div className={cn(
            "h-1.5 rounded-full bg-primary/30 w-16 overflow-hidden"
          )}>
            <div
              className="h-full bg-primary rounded-full"
              style={{ width: `${item.conviction}%` }}
            />
          </div>
          <span className="text-[10px] font-bold text-muted-foreground">{item.conviction}</span>
        </div>
      </td>
      <td className="py-3 px-4">
        <span className={cn("text-[10px] font-black px-2 py-1 rounded-md", cfg.cls)}>
          {cfg.emoji} {cfg.label}
        </span>
        {item.resolved_price && (
          <span className="ml-1 text-[10px] text-muted-foreground font-mono">
            @ ${formatPrice(item.resolved_price)}
          </span>
        )}
      </td>
      <td className="py-3 px-4 text-muted-foreground">{timeAgo(item.fired_at)}</td>
      <td className="py-3 px-4">
        <div className="flex flex-col gap-1">
          <span className={cn(
            "text-[10px] font-bold px-1.5 py-0.5 rounded w-fit",
            item.market_state === "VOLATILE" ? "bg-red-500/10 text-red-500" :
            item.market_state === "TRENDING" ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400" :
            "bg-secondary text-muted-foreground"
          )}>
            {item.market_state}
          </span>
          <span className={cn(
            "text-[9px] font-bold px-1.5 py-0.5 rounded w-fit uppercase",
            item.source === "backtest"
              ? "bg-amber-500/10 text-amber-600 dark:text-amber-400"
              : "bg-sky-500/10 text-sky-600 dark:text-sky-400"
          )}>
            {item.source}
          </span>
        </div>
      </td>
    </tr>
  );
}

const ALL_COINS = [
  { key: "BTCUSDT", label: "BTC" },
  { key: "ETHUSDT", label: "ETH" },
  { key: "BNBUSDT", label: "BNB" },
  { key: "TRXUSDT", label: "TRX" },
  { key: "XRPUSDT", label: "XRP" },
  { key: "FETUSDT", label: "FET" },
  { key: "NEARUSDT", label: "NEAR" },
  { key: "ARBUSDT", label: "ARB" },
  { key: "ATOMUSDT", label: "ATOM" },
  { key: "DOGEUSDT", label: "DOGE" },
  { key: "APTUSDT", label: "APT" },
];

function SettingsPanel({ config, onSave, isSaving, saved }: {
  config: SignalLogConfig;
  onSave: (c: SignalLogConfig) => void;
  isSaving: boolean;
  saved: boolean;
}) {
  const [draft, setDraft] = useState<SignalLogConfig>(config);

  const toggleCoin = (key: string) => {
    setDraft(d => ({
      ...d,
      watchlist: d.watchlist.includes(key)
        ? d.watchlist.filter(k => k !== key)
        : [...d.watchlist, key],
    }));
  };

  const toggleBool = (field: keyof SignalLogConfig) => {
    setDraft(d => ({ ...d, [field]: !d[field] }));
  };

  return (
    <div className="bg-secondary/30 rounded-2xl border border-border/40 p-4 space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Watchlist */}
        <div className="space-y-2">
          <div className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Watchlist</div>
          <div className="flex flex-wrap gap-1.5">
            {ALL_COINS.map(c => (
              <button
                key={c.key}
                onClick={() => toggleCoin(c.key)}
                className={cn(
                  "px-2.5 py-1 rounded-lg text-[11px] font-black transition-all",
                  draft.watchlist.includes(c.key)
                    ? "bg-primary text-primary-foreground"
                    : "bg-secondary/60 text-muted-foreground hover:bg-secondary"
                )}
              >
                {c.label}
              </button>
            ))}
          </div>
        </div>

        {/* Number inputs */}
        <div className="space-y-2">
          <div className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Parameters</div>
          <div className="flex flex-col gap-2">
            <label className="flex items-center justify-between gap-2 text-[11px]">
              <span className="text-muted-foreground">Min Confidence</span>
              <input
                type="number"
                min={0} max={100} step={5}
                value={draft.min_titan_confidence}
                onChange={e => setDraft(d => ({ ...d, min_titan_confidence: Number(e.target.value) }))}
                className="w-16 bg-secondary/60 border border-border/40 rounded-lg px-2 py-1 text-[11px] font-mono text-center"
              />
            </label>
            <label className="flex items-center justify-between gap-2 text-[11px]">
              <span className="text-muted-foreground">Review Days</span>
              <input
                type="number"
                min={1} max={30}
                value={draft.review_days}
                onChange={e => setDraft(d => ({ ...d, review_days: Number(e.target.value) }))}
                className="w-16 bg-secondary/60 border border-border/40 rounded-lg px-2 py-1 text-[11px] font-mono text-center"
              />
            </label>
          </div>
        </div>

        {/* Market gates */}
        <div className="space-y-2">
          <div className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Market Gates</div>
          <div className="flex flex-col gap-1.5">
            {[
              { field: "block_sleeping" as const, label: "Block SLEEPING" },
              { field: "block_volatile" as const, label: "Block VOLATILE" },
              { field: "macro_guard" as const, label: "Macro Guard" },
              { field: "block_btc_sell" as const, label: "Block BTC Sell" },
            ].map(({ field, label }) => (
              <button
                key={field}
                onClick={() => toggleBool(field)}
                className="flex items-center gap-2 text-[11px] text-left"
              >
                <div className={cn(
                  "w-7 h-4 rounded-full transition-colors flex items-center px-0.5",
                  draft[field] ? "bg-primary justify-end" : "bg-secondary/80 justify-start"
                )}>
                  <div className="w-3 h-3 rounded-full bg-white shadow-sm" />
                </div>
                <span className={cn(
                  "font-bold",
                  draft[field] ? "text-foreground" : "text-muted-foreground"
                )}>{label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Save */}
      <div className="flex justify-end">
        <button
          onClick={() => onSave(draft)}
          disabled={isSaving}
          className={cn(
            "flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-[11px] font-black transition-all",
            saved
              ? "bg-emerald-500/20 text-emerald-500"
              : "bg-primary text-primary-foreground hover:opacity-90"
          )}
        >
          {saved ? <Check size={12} /> : <Save size={12} />}
          {saved ? "Saved" : isSaving ? "Saving..." : "Save Settings"}
        </button>
      </div>
    </div>
  );
}

export function SignalLog() {
  const [activeSymbol, setActiveSymbol] = useState("All");
  const [activeSource, setActiveSource] = useState("All");
  const [showSettings, setShowSettings] = useState(false);
  const [saved, setSaved] = useState(false);
  const { data: config } = useSignalLogConfig();
  const updateConfig = useUpdateSignalLogConfig();
  const { data, isLoading, isError, refetch, isFetching } = useSignalLog(
    activeSymbol === "All" ? undefined : activeSymbol,
    activeSource === "All" ? undefined : activeSource.toLowerCase(),
    100
  );

  const handleSave = (draft: SignalLogConfig) => {
    updateConfig.mutate(draft, {
      onSuccess: () => {
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
      },
    });
  };

  const summary = data?.summary;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex flex-wrap gap-2">
          {SYMBOLS.map((sym) => (
            <button
              key={sym}
              onClick={() => setActiveSymbol(sym)}
              className={cn(
                "px-3 py-1.5 rounded-lg text-[11px] font-black uppercase tracking-wider transition-all",
                activeSymbol === sym
                  ? "bg-primary text-primary-foreground shadow-md"
                  : "bg-secondary/40 text-muted-foreground hover:text-foreground hover:bg-secondary/70"
              )}
            >
              {sym}
            </button>
          ))}
          <div className="w-px bg-border/50 mx-1" />
          {SOURCES.map((src) => (
            <button
              key={src}
              onClick={() => setActiveSource(src)}
              className={cn(
                "px-3 py-1.5 rounded-lg text-[11px] font-black uppercase tracking-wider transition-all",
                activeSource === src
                  ? src === "Backtest" ? "bg-amber-500/20 text-amber-600 dark:text-amber-400 border border-amber-500/40"
                    : src === "Live" ? "bg-sky-500/20 text-sky-600 dark:text-sky-400 border border-sky-500/40"
                    : "bg-primary text-primary-foreground shadow-md"
                  : "bg-secondary/40 text-muted-foreground hover:text-foreground hover:bg-secondary/70"
              )}
            >
              {src}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowSettings(!showSettings)}
            className={cn(
              "flex items-center gap-1.5 text-[11px] transition-colors",
              showSettings ? "text-primary" : "text-muted-foreground hover:text-foreground"
            )}
          >
            <Settings2 size={12} />
            Settings
          </button>
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="flex items-center gap-1.5 text-[11px] text-muted-foreground hover:text-foreground transition-colors"
          >
            <RefreshCw size={12} className={isFetching ? "animate-spin" : ""} />
            Refresh
          </button>
        </div>
      </div>

      {/* Settings panel */}
      {showSettings && config && (
        <SettingsPanel
          config={config}
          onSave={handleSave}
          isSaving={updateConfig.isPending}
          saved={saved}
        />
      )}

      {/* Summary bar */}
      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          {[
            { label: "Total", value: summary.total, cls: "text-foreground" },
            { label: "Open", value: summary.open, cls: "text-sky-500 dark:text-sky-400" },
            { label: "Win", value: summary.win, cls: "text-emerald-500 dark:text-emerald-400" },
            { label: "Loss", value: summary.loss, cls: "text-red-500 dark:text-red-400" },
            {
              label: "Win Rate",
              value: summary.win_rate !== null ? `${summary.win_rate}%` : "—",
              cls: summary.win_rate !== null
                ? summary.win_rate >= 50 ? "text-emerald-500 dark:text-emerald-400"
                : summary.win_rate >= 33 ? "text-amber-500 dark:text-amber-400"
                : "text-red-500 dark:text-red-400"
                : "text-muted-foreground",
            },
          ].map(({ label, value, cls }) => (
            <div key={label} className="bg-secondary/30 rounded-xl p-3 border border-border/40 text-center">
              <div className={cn("text-xl font-black", cls)}>{value}</div>
              <div className="text-[10px] text-muted-foreground font-bold uppercase tracking-widest mt-0.5">{label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Table */}
      {isLoading ? (
        <div className="h-48 flex items-center justify-center text-muted-foreground text-sm">Loading signal log…</div>
      ) : isError ? (
        <div className="h-48 flex items-center justify-center text-red-500 text-sm">Failed to load signal log.</div>
      ) : !data?.data.length ? (
        <div className="h-48 flex flex-col items-center justify-center text-muted-foreground text-sm gap-2">
          <span className="text-3xl">📭</span>
          <span>No signals logged yet. The worker logs setups every 5 minutes.</span>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-border/40">
          <table className="w-full">
            <thead>
              <tr className="bg-secondary/40 border-b border-border/40 text-[10px] font-black uppercase tracking-widest text-muted-foreground">
                <th className="py-3 px-4 text-left">Symbol</th>
                <th className="py-3 px-4 text-left">Entry</th>
                <th className="py-3 px-4 text-left">TP</th>
                <th className="py-3 px-4 text-left">SL</th>
                <th className="py-3 px-4 text-left">Conv.</th>
                <th className="py-3 px-4 text-left">Outcome</th>
                <th className="py-3 px-4 text-left">Age</th>
                <th className="py-3 px-4 text-left">Mkt State</th>
              </tr>
            </thead>
            <tbody>
              {data.data.map((item) => (
                <SignalRow key={item.id} item={item} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
