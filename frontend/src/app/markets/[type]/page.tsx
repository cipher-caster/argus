"use client";

import { CoinTable } from "@/components/features/dashboard/CoinTable";
import { useCoins } from "@/hooks/useMarketOverview";
import { ChevronRight } from "lucide-react";
import { useParams } from "next/navigation";
import { useState } from "react";

export default function MarketCategoryPage() {
  const params = useParams();
  const type = params.type as string;

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");

  const getDefaultSort = () => {
    switch (type) {
      case "gainers":
        return { sortBy: "change_24h", sortOrder: "desc" };
      case "losers":
        return { sortBy: "change_24h", sortOrder: "asc" };
      case "volume":
        return { sortBy: "volume_24h", sortOrder: "desc" };
      default:
        return { sortBy: "price", sortOrder: "desc" };
    }
  };

  const defaultSort = getDefaultSort();
  const [sortBy, setSortBy] = useState(defaultSort.sortBy);
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">(defaultSort.sortOrder as "asc" | "desc");
  const pageSize = 50;

  const { data: coinsData, isLoading } = useCoins({
    page,
    pageSize,
    search: search || undefined,
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

  const getTitle = () => {
    switch (type) {
      case "gainers":
        return "Top Gainers";
      case "losers":
        return "Top Losers";
      case "volume":
        return "Volume Leaders";
      default:
        return "Market Data";
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <main className="max-w-[1440px] mx-auto p-6 md:p-8 space-y-6">
        <div className="flex items-center justify-between animate-in fade-in slide-in-from-top-2 duration-500">
          <div className="space-y-1">
            <h1 className="text-3xl font-black tracking-tight italic uppercase">{getTitle()}</h1>
            <p className="text-sm text-muted-foreground font-medium tracking-wide uppercase opacity-70">All coins • Sorted by {sortBy.replace("_", " ")}</p>
          </div>
        </div>

        <section className="bg-secondary/30 rounded-2xl overflow-hidden border border-border/50">
          <CoinTable coins={coinsData?.coins || []} isLoading={isLoading} sortBy={sortBy} sortOrder={sortOrder} onSort={handleSort} />

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-4 py-6 border-t border-border/30">
              <div className="flex items-center gap-1 bg-muted/30 p-1 rounded-xl border border-border/50">
                <button className="px-3 py-1.5 text-xs font-bold rounded-lg hover:bg-muted transition-all disabled:opacity-30 disabled:pointer-events-none" onClick={() => setPage(1)} disabled={page === 1}>
                  First
                </button>
                <button className="px-3 py-1.5 text-xs font-bold rounded-lg hover:bg-muted transition-all disabled:opacity-30 disabled:pointer-events-none flex items-center gap-1" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}>
                  <ChevronRight size={12} className="rotate-180" /> Prev
                </button>
                <div className="px-4 text-xs font-bold border-x border-border/50">
                  <span className="text-muted-foreground">Page </span>
                  <span>{page}</span>
                  <span className="text-muted-foreground"> / {totalPages}</span>
                </div>
                <button className="px-3 py-1.5 text-xs font-bold rounded-lg hover:bg-muted transition-all disabled:opacity-30 disabled:pointer-events-none flex items-center gap-1" onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page >= totalPages}>
                  Next <ChevronRight size={12} />
                </button>
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
