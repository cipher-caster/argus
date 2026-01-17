"use client";

/**
 * Argus Dashboard
 * Professional CoinGlass-style layout
 */

import { CoinTable } from "@/components/features/dashboard/CoinTable";
import { MarketIndicators } from "@/components/features/dashboard/MarketIndicators";
import { TopCoinsWidgets } from "@/components/features/dashboard/TopCoinsWidgets";
import { OracleSignalSummary } from "@/components/OracleSignalSummary";
import { useProvider } from "@/hooks/useMarketData";
import { useCoins, useMarketSummary } from "@/hooks/useMarketOverview";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { ChevronLeft, ChevronRight } from "lucide-react";

export default function MarketOverview() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // State: Initialize from URL on creation
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState(() => searchParams.get("sort_by") || "market_cap");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">(() => (searchParams.get("sort_order") as "asc" | "desc") || "desc");
  const pageSize = 50;

  // Cleanup URL on mount if it contains sort params (as requested)
  useEffect(() => {
    if (searchParams.has("sort_by") || searchParams.has("sort_order")) {
      // Clean URL without triggering a re-render/refetch via Next.js router
      window.history.replaceState({}, "", window.location.pathname);
    }
  }, []);

  const { data: providerData } = useProvider();
  const { data: summary } = useMarketSummary();
  const { data: coinsData, isLoading } = useCoins({
    page,
    pageSize,
    sortBy,
    sortOrder,
  });

  const handleSort = (field: string) => {
    let newOrder: "asc" | "desc" = "desc";
    if (sortBy === field) {
      newOrder = sortOrder === "asc" ? "desc" : "asc";
    } else {
      newOrder = "desc"; // Default to desc for new field
    }

    // Update Local State ONLY (Instant Feedback, Clean URL)
    setSortBy(field);
    setSortOrder(newOrder);
    setPage(1);
  };

  const totalPages = coinsData ? Math.ceil(coinsData.total / pageSize) : 1;

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Main Content */}
      <main className="max-w-[1440px] mx-auto p-6 md:p-8 space-y-10">
        {/* Market Indicators */}
        <section className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
          <div className="lg:col-span-2 h-full">
            <MarketIndicators />
          </div>
          <div className="lg:col-span-1 h-full">
            <OracleSignalSummary />
          </div>
        </section>

        {/* Widgets Section */}
        <section className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-100">
          <h2 className="text-2xl font-extrabold tracking-tight">Data Analysis</h2>
          <TopCoinsWidgets gainers={summary?.top_gainers || []} losers={summary?.top_losers || []} volume={summary?.top_volume || []} isLoading={!summary} />
        </section>

        {/* Main Table */}
        <section className="space-y-6 animate-in fade-in slide-in-from-bottom-6 duration-1000 delay-200">
          <div className="bg-secondary/30 rounded-2xl p-1 overflow-hidden">
            <CoinTable coins={coinsData?.coins || []} isLoading={isLoading} sortBy={sortBy} sortOrder={sortOrder} onSort={handleSort} />
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-4 py-8">
              <div className="flex items-center gap-1 bg-muted/30 p-1.5 rounded-xl border border-border/50">
                <button className="px-4 py-2 text-xs font-bold rounded-lg transition-all hover:bg-muted disabled:opacity-30 disabled:pointer-events-none" onClick={() => setPage(1)} disabled={page === 1}>
                  First
                </button>
                <button
                  className="px-4 py-2 text-xs font-bold rounded-lg transition-all hover:bg-muted disabled:opacity-30 disabled:pointer-events-none flex items-center gap-1"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  <ChevronLeft size={14} /> Prev
                </button>
                <div className="px-6 text-xs font-bold border-x border-border/50">
                  <span className="text-muted-foreground mr-1">Page</span>
                  <span className="text-foreground">{page}</span>
                  <span className="text-muted-foreground mx-1">/</span>
                  <span className="text-muted-foreground">{totalPages}</span>
                </div>
                <button
                  className="px-4 py-2 text-xs font-bold rounded-lg transition-all hover:bg-muted disabled:opacity-30 disabled:pointer-events-none flex items-center gap-1"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                >
                  Next <ChevronRight size={14} />
                </button>
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
