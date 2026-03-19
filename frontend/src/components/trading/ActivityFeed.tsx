"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchActivityLog, type ActivityLogItem } from "@/lib/api";
import { Activity, AlertTriangle, CheckCircle, Power, RefreshCw, Zap } from "lucide-react";

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
  const { data, isLoading } = useQuery({
    queryKey: ["activity-log"],
    queryFn: () => fetchActivityLog(30),
    staleTime: 60_000,
    refetchInterval: 60_000,
  });

  const events = data?.data ?? [];

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Activity size={16} className="text-primary" />
        <h3 className="text-xs font-black uppercase tracking-widest">System Activity</h3>
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
        </div>
      )}
    </div>
  );
}
