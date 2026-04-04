"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { fetchActivityLog, type ActivityLogItem } from "@/lib/api";
import { Activity, AlertTriangle, CheckCircle, Power, RefreshCw, Zap } from "lucide-react";

const PAGE_SIZE = 30;

const EVENT_CONFIG: Record<string, { icon: React.ElementType; color: string; label: string }> = {
  STARTUP: { icon: Power, color: "text-green-400", label: "System Start" },
  SHUTDOWN: { icon: Power, color: "text-zinc-400", label: "System Stop" },
  HEARTBEAT_GAP: { icon: AlertTriangle, color: "text-amber-400", label: "Downtime Detected" },
  RECOVERY_SCAN: { icon: RefreshCw, color: "text-blue-400", label: "Recovery Scan" },
  SIGNAL_RECOVERED: { icon: Zap, color: "text-violet-400", label: "Signal Recovered" },
  OUTCOME_RESOLVED: { icon: CheckCircle, color: "text-emerald-400", label: "Outcome Resolved" },
  POSITION_RECOVERED: { icon: RefreshCw, color: "text-cyan-400", label: "Position Recovered" },
  ERROR: { icon: AlertTriangle, color: "text-red-400", label: "Error" },
};

function formatTime(ms: number): string {
  const date = new Date(ms);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function parseDetails(details: string | null): Record<string, unknown> {
  if (!details) return {};
  try {
    return JSON.parse(details);
  } catch {
    return { message: details };
  }
}

function DetailsSummary({ event }: { event: ActivityLogItem }) {
  const d = parseDetails(event.details);

  switch (event.event_type) {
    case "HEARTBEAT_GAP":
      return <span>Offline for {d.gap_hours as number}h</span>;
    case "RECOVERY_SCAN":
      if ((d.signals_recovered as number | undefined) !== undefined) {
        return (
          <span>
            {d.signals_recovered as number} signal(s) recovered from {(d.missed_closes as number) || "?"} missed close(s)
          </span>
        );
      }
      return <span>{d.missed_closes as number} missed candle close(s) detected</span>;
    case "SIGNAL_RECOVERED":
      return (
        <span>
          {d.symbol as string} {d.direction as string} — conviction {d.conviction as number}
        </span>
      );
    case "OUTCOME_RESOLVED":
      return (
        <span>
          {d.symbol as string} {d.direction as string} → {d.outcome as string} @{" "}
          ${(d.resolved_price as number)?.toLocaleString()}
        </span>
      );
    case "STARTUP":
    case "SHUTDOWN":
      return <span>{(d.message as string) || ""}</span>;
    default:
      return <span>{(d.message as string) || JSON.stringify(d)}</span>;
  }
}

export function ActivityFeed() {
  const [events, setEvents] = useState<ActivityLogItem[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isFetchingMore, setIsFetchingMore] = useState(false);
  const sentinelRef = useRef<HTMLDivElement>(null);
  const hasMore = events.length < total;

  const loadPage = useCallback(async (pageOffset: number, replace: boolean) => {
    if (replace) setIsLoading(true);
    else setIsFetchingMore(true);
    try {
      const res = await fetchActivityLog(PAGE_SIZE, pageOffset);
      setTotal(res.total);
      setEvents(prev => replace ? res.data : [...prev, ...res.data]);
      setOffset(pageOffset + res.data.length);
    } finally {
      if (replace) setIsLoading(false);
      else setIsFetchingMore(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    loadPage(0, true);
  }, [loadPage]);

  // Refresh every 60s (only first page — prepend new items)
  useEffect(() => {
    const id = setInterval(() => loadPage(0, true), 60_000);
    return () => clearInterval(id);
  }, [loadPage]);

  // Infinite scroll sentinel
  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !isFetchingMore) {
          loadPage(offset, false);
        }
      },
      { threshold: 0.1 }
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [hasMore, isFetchingMore, offset, loadPage]);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity size={16} className="text-primary" />
          <h3 className="text-xs font-black uppercase tracking-widest">System Activity</h3>
        </div>
        {total > 0 && (
          <span className="text-[10px] text-muted-foreground">{total} events</span>
        )}
      </div>

      {isLoading ? (
        <div className="text-xs text-muted-foreground py-4 text-center">Loading activity...</div>
      ) : events.length === 0 ? (
        <div className="text-xs text-muted-foreground py-4 text-center">No activity recorded yet</div>
      ) : (
        <div className="space-y-1 max-h-[400px] overflow-y-auto pr-1">
          {events.map((event) => {
            const config = EVENT_CONFIG[event.event_type] ?? EVENT_CONFIG.ERROR;
            const Icon = config.icon;
            const isSevere = event.severity === "ERROR" || event.severity === "WARN";

            return (
              <div
                key={event.id}
                className={`flex items-start gap-2.5 px-3 py-2 rounded-lg text-xs transition-colors ${
                  isSevere ? "bg-amber-500/5 border border-amber-500/10" : "hover:bg-white/[0.02]"
                }`}
              >
                <Icon size={14} className={`${config.color} mt-0.5 shrink-0`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className={`font-bold ${config.color}`}>{config.label}</span>
                    <span className="text-muted-foreground/50">·</span>
                    <span className="text-muted-foreground/70">{formatTime(event.timestamp)}</span>
                  </div>
                  <div className="text-muted-foreground mt-0.5 truncate">
                    <DetailsSummary event={event} />
                  </div>
                </div>
              </div>
            );
          })}

          {/* Sentinel for infinite scroll */}
          <div ref={sentinelRef} className="h-4 flex items-center justify-center">
            {isFetchingMore && (
              <span className="text-[10px] text-muted-foreground">Loading more...</span>
            )}
            {!hasMore && events.length > PAGE_SIZE && (
              <span className="text-[10px] text-muted-foreground/40">All events loaded</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
