"use client";

/**
 * Argus Dashboard
 * Professional CoinGlass-style layout
 */

import { CoinTable } from "@/components/features/dashboard/CoinTable";
import { MarketIndicators } from "@/components/features/dashboard/MarketIndicators";
import { TopCoinsWidgets } from "@/components/features/dashboard/TopCoinsWidgets";
import { useProvider } from "@/hooks/useMarketData";
import { useCoins, useMarketSummary } from "@/hooks/useMarketOverview";
import { useState } from "react";

import { ChevronLeft, ChevronRight } from "lucide-react";

export default function MarketOverview() {
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState("market_cap");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const pageSize = 50;

  const { data: providerData } = useProvider();
  const { data: summary } = useMarketSummary();
  const { data: coinsData, isLoading } = useCoins({
    page,
    pageSize,
    sortBy,
    sortOrder,
  });

  const handleSort = (field: string) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortBy(field);
      setSortOrder("desc");
    }
    setPage(1);
  };

  const totalPages = coinsData ? Math.ceil(coinsData.total / pageSize) : 1;

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Main Content */}
      <main className="max-w-[1440px] mx-auto p-6 md:p-8 space-y-10">
        {/* Market Indicators */}
        <section className="animate-in fade-in slide-in-from-bottom-2 duration-500">
          <MarketIndicators />
        </section>

        {/* Widgets Section */}
        <section className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-100">
          <h2 className="text-2xl font-extrabold tracking-tight">Data Analysis</h2>
          <TopCoinsWidgets coins={coinsData?.coins || []} isLoading={isLoading} />
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
