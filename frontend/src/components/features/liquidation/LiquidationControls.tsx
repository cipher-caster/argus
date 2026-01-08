"use client";

/**
 * Controls for the liquidation heatmap page
 */

import { formatNumber } from "@/lib/formatters";
import { RefreshCw } from "lucide-react";

// ... (skip lines)

        <span className="text-xs font-mono text-muted-foreground w-10">{formatNumber(threshold)}</span>
      </div>

      {/* Refresh Button */}
      <button onClick={onRefresh} disabled={isRefreshing} className="p-2 rounded-lg bg-muted/50 hover:bg-muted transition-colors disabled:opacity-50">
        <RefreshCw size={16} className={isRefreshing ? "animate-spin" : ""} />
      </button>
    </div>
  );
}
