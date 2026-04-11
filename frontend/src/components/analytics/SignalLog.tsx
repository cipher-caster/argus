"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useSignalLog, useSignalLogConfig, useUpdateSignalLogConfig, useScanStatus, useRegime } from "@/hooks/useAnalyticsData";
import { SignalLogItem, SignalLogConfig } from "@/lib/api";
import { formatPriceCompact, formatDateTime, formatPercentageChange, timeAgo } from "@/lib/formatters";
import { OUTCOME_CONFIG } from "@/lib/outcomeConfig";
import { cn } from "@/lib/utils";
import { RefreshCw, Settings2, Save, Check, ChevronDown } from "lucide-react";
import { SignalDetailModal } from "./SignalDetailModal";

const SYMBOLS = ["All", "BTC", "ETH", "BNB", "TRX", "XRP", "FET", "NEAR", "ARB", "ATOM", "DOGE", "APT"];
const SOURCES = ["All", "Live", "Scanner", "Backtest"];

// formatPriceCompact and formatDateTime imported from @/lib/formatters

function SignalRow({ item, onClick }: { item: SignalLogItem; onClick: () => void }) {
  const cfg = OUTCOME_CONFIG[item.outcome] ?? OUTCOME_CONFIG.OPEN;
  const isLong = item.direction === "LONG";
  const base = item.symbol.replace("USDT", "");

  return (
    <tr className="border-b border-border/30 hover:bg-secondary/20 transition-colors text-[12px] cursor-pointer" onClick={onClick}>
      <td className="py-3 px-4 font-black tracking-tight">
        <Link
          href={`/chart/${base}-USDT`}
          onClick={(e) => e.stopPropagation()}
          className={cn("font-bold hover:underline", isLong ? "text-emerald-500 dark:text-emerald-400" : "text-red-500 dark:text-red-400")}
        >
          {base}
        </Link>
        <span className={cn(
          "ml-2 text-[10px] font-black px-1.5 py-0.5 rounded",
          isLong ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400" : "bg-red-500/10 text-red-600 dark:text-red-400"
        )}>
          {item.direction}
        </span>
        {item.source === "backtest" && item.provider && (
          <span className="ml-1 text-[10px] font-bold px-1.5 py-0.5 rounded bg-zinc-500/10 text-zinc-500">
            {item.provider}
          </span>
        )}
      </td>
      <td className="py-3 px-4 font-mono text-muted-foreground">${formatPriceCompact(item.entry)}</td>
      <td className="py-3 px-4 font-mono text-emerald-600 dark:text-emerald-400">
        ${formatPriceCompact(item.tp)}
        <span className="ml-1 text-[10px] opacity-60">{formatPercentageChange(item.entry, item.tp, item.direction)}</span>
      </td>
      <td className="py-3 px-4 font-mono text-red-600 dark:text-red-400">
        ${formatPriceCompact(item.sl)}
        <span className="ml-1 text-[10px] opacity-60">{formatPercentageChange(item.entry, item.sl, item.direction)}</span>
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
            @ ${formatPriceCompact(item.resolved_price)}
          </span>
        )}
      </td>
      <td className="py-3 px-4 text-muted-foreground whitespace-nowrap">{formatDateTime(item.fired_at)}</td>
      <td className="py-3 px-4 text-muted-foreground whitespace-nowrap">
        {item.resolved_at ? formatDateTime(item.resolved_at) : "—"}
      </td>
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
              : item.source === "scanner"
              ? "bg-violet-500/10 text-violet-600 dark:text-violet-400"
              : item.source === "counter"
              ? "bg-zinc-500/10 text-zinc-500 dark:text-zinc-400"
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

const PROVIDERS = ["All", "Binance", "OKX"];

function getNextScanMs(): number {
  const now = new Date();
  const scanHours = [0, 4, 8, 12, 16, 20];
  for (const h of scanHours) {
    const candidate = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate(), h, 3);
    if (candidate > Date.now()) return candidate;
  }
  const tomorrow = new Date(now);
  tomorrow.setUTCDate(tomorrow.getUTCDate() + 1);
  return Date.UTC(tomorrow.getUTCFullYear(), tomorrow.getUTCMonth(), tomorrow.getUTCDate(), 0, 3);
}

function formatCountdown(ms: number): string {
  const diff = ms - Date.now();
  if (diff <= 0) return "soon";
  const mins = Math.floor(diff / 60_000);
  if (mins < 60) return `${mins}m`;
  const hrs = Math.floor(mins / 60);
  const rem = mins % 60;
  return rem > 0 ? `${hrs}h ${rem}m` : `${hrs}h`;
}

export function SignalLog() {
  const PAGE_SIZE = 50;
  const [activeSymbol, setActiveSymbol] = useState("All");
  const [activeSource, setActiveSource] = useState("All");
  const [activeProvider, setActiveProvider] = useState("All");
  const [page, setPage] = useState(1);
  const [showSettings, setShowSettings] = useState(false);
  const [saved, setSaved] = useState(false);
  const [selectedSignal, setSelectedSignal] = useState<SignalLogItem | null>(null);
  const { data: config } = useSignalLogConfig();
  const updateConfig = useUpdateSignalLogConfig();
  const { data: scanStatus } = useScanStatus();
  const { data: regime } = useRegime("4h");
  const offset = (page - 1) * PAGE_SIZE;
  const { data, isLoading, isError, refetch, isFetching } = useSignalLog(
    activeSymbol === "All" ? undefined : activeSymbol,
    activeSource === "All" ? undefined : activeSource.toLowerCase(),
    PAGE_SIZE,
    offset,
    activeProvider === "All" ? undefined : activeProvider.toLowerCase()
  );

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 1;

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
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative">
            <select
              value={activeSymbol}
              onChange={(e) => { setActiveSymbol(e.target.value); setPage(1); }}
              className="appearance-none bg-secondary/40 border border-border/50 rounded-lg px-3 py-1.5 pr-7 text-[11px] font-black uppercase tracking-wider cursor-pointer hover:bg-secondary/70 transition-all focus:outline-none focus:ring-1 focus:ring-primary"
            >
              {SYMBOLS.map((sym) => (
                <option key={sym} value={sym}>{sym}</option>
              ))}
            </select>
            <ChevronDown size={10} className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none text-muted-foreground" />
          </div>
          <div className="w-px h-6 bg-border/50" />
          {SOURCES.map((src) => (
            <button
              key={src}
              onClick={() => { setActiveSource(src); setPage(1); }}
              className={cn(
                "px-3 py-1.5 rounded-lg text-[11px] font-black uppercase tracking-wider transition-all",
                activeSource === src
                  ? src === "Backtest" ? "bg-amber-500/20 text-amber-600 dark:text-amber-400 border border-amber-500/40"
                    : src === "Scanner" ? "bg-violet-500/20 text-violet-600 dark:text-violet-400 border border-violet-500/40"
                    : src === "Live" ? "bg-sky-500/20 text-sky-600 dark:text-sky-400 border border-sky-500/40"
                    : "bg-primary text-primary-foreground shadow-md"
                  : "bg-secondary/40 text-muted-foreground hover:text-foreground hover:bg-secondary/70"
              )}
            >
              {src}
            </button>
          ))}
          <div className="w-px h-6 bg-border/50" />
          {PROVIDERS.map((p) => (
            <button
              key={p}
              onClick={() => { setActiveProvider(p); setPage(1); }}
              className={cn(
                "px-2 py-1 text-xs rounded capitalize transition-all",
                activeProvider === p
                  ? "bg-zinc-700 text-white"
                  : "text-zinc-400 hover:text-zinc-200"
              )}
            >
              {p}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-3">
          {activeSource === "Live" && scanStatus?.available && scanStatus.timestamp_ms != null && (
            <span className="text-[11px] text-muted-foreground hidden sm:inline">
              Scanned {timeAgo(scanStatus.timestamp_ms)}
              {(scanStatus.skipped_regime ?? 0) > 0 && (
                <> · <span className="text-amber-500/80">{scanStatus.skipped_regime} blocked</span></>
              )}
              {" · "}next {formatCountdown(getNextScanMs())}
            </span>
          )}
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
        <div className="grid grid-cols-2 sm:grid-cols-6 gap-3">
          {[
            { label: "Total", value: summary.total, cls: "text-foreground" },
            { label: "Open", value: summary.open, cls: "text-sky-500 dark:text-sky-400" },
            { label: "Win", value: summary.win, cls: "text-emerald-500 dark:text-emerald-400" },
            { label: "Loss", value: summary.loss, cls: "text-red-500 dark:text-red-400" },
            { label: "Rejected", value: summary.rejected ?? 0, cls: "text-zinc-500 dark:text-zinc-400" },
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
          {activeSource === "Live" && regime?.regime && (scanStatus?.skipped_regime ?? 0) > 0 ? (
            <>
              <span className="font-medium text-foreground">
                {regime.regime} regime — watchlist {regime.regime === "BEAR" ? "longs" : "shorts"} blocked
              </span>
              <span className="text-xs text-center max-w-sm">
                Live signals resume when a watchlist coin generates a {regime.regime === "BEAR" ? "SHORT" : "LONG"},
                or BTC flips the weekly EMA50 ({regime.regime === "BEAR" ? "closes above" : "closes below"} ${regime.ema50?.toLocaleString()}).
              </span>
              {scanStatus?.timestamp_ms != null && (
                <span className="text-xs text-muted-foreground/60">
                  Last scan {timeAgo(scanStatus.timestamp_ms)} · {scanStatus.skipped_regime} blocked · next {formatCountdown(getNextScanMs())}
                </span>
              )}
            </>
          ) : (
            <>
              <span className="text-3xl">📭</span>
              <span>No signals logged yet. The worker logs setups at 4H candle closes.</span>
            </>
          )}
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
                <th className="py-3 px-4 text-left">Fired</th>
                <th className="py-3 px-4 text-left">Resolved</th>
                <th className="py-3 px-4 text-left">Mkt State</th>
              </tr>
            </thead>
            <tbody>
              {data.data.map((item) => (
                <SignalRow key={item.id} item={item} onClick={() => setSelectedSignal(item)} />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-4 pt-2">
          <div className="flex items-center gap-1 bg-muted/30 p-1 rounded-xl border border-border/50">
            <button
              className="px-3 py-1.5 text-xs font-bold rounded-lg hover:bg-muted transition-all disabled:opacity-30 disabled:pointer-events-none"
              onClick={() => setPage(1)}
              disabled={page === 1}
            >
              First
            </button>
            <button
              className="px-3 py-1.5 text-xs font-bold rounded-lg hover:bg-muted transition-all disabled:opacity-30 disabled:pointer-events-none flex items-center gap-1"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
            >
              <ChevronDown size={12} className="rotate-90" /> Prev
            </button>
            <div className="px-4 text-xs font-bold border-x border-border/50">
              <span className="text-muted-foreground">Page </span>
              <span>{page}</span>
              <span className="text-muted-foreground"> / {totalPages}</span>
            </div>
            <button
              className="px-3 py-1.5 text-xs font-bold rounded-lg hover:bg-muted transition-all disabled:opacity-30 disabled:pointer-events-none flex items-center gap-1"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
            >
              Next <ChevronDown size={12} className="-rotate-90" />
            </button>
          </div>
        </div>
      )}

      {/* Signal detail modal */}
      <SignalDetailModal
        isOpen={selectedSignal !== null}
        onClose={() => setSelectedSignal(null)}
        signal={selectedSignal}
      />
    </div>
  );
}
