"use client";

import { CoinTable } from "@/components/CoinTable";
import { useCoins } from "@/hooks/useMarketOverview";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
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
    <div className="min-h-screen bg-background">
      <main className="max-w-[1440px] mx-auto p-6">
        <div className="mb-6">
          <Link href="/" className="inline-flex items-center gap-1.5 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors mb-4 group">
            <ArrowLeft size={16} className="group-hover:-translate-x-0.5 transition-transform" />
            Back to Overview
          </Link>
          <h1 className="text-3xl font-bold text-foreground tracking-tight">{getTitle()}</h1>
        </div>

        <section className="bg-card border border-border rounded-2xl shadow-sm overflow-hidden">
          <CoinTable coins={coinsData?.coins || []} isLoading={isLoading} sortBy={sortBy} sortOrder={sortOrder} onSort={handleSort} />

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-center items-center gap-4 py-8 border-t border-border">
              <div className="flex items-center gap-1">
                <button
                  className="px-4 py-2 text-sm font-bold bg-secondary border border-border rounded-xl hover:bg-muted disabled:opacity-40 disabled:cursor-not-allowed transition-all active:scale-95"
                  onClick={() => setPage(1)}
                  disabled={page === 1}
                >
                  First
                </button>
                <button
                  className="px-4 py-2 text-sm font-bold bg-secondary border border-border rounded-xl hover:bg-muted disabled:opacity-40 disabled:cursor-not-allowed transition-all active:scale-95"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  Prev
                </button>
              </div>

              <span className="text-sm font-medium text-muted-foreground">
                Page <strong className="text-foreground">{page}</strong> of <strong className="text-foreground">{totalPages}</strong>
              </span>

              <div className="flex items-center gap-1">
                <button
                  className="px-4 py-2 text-sm font-bold bg-secondary border border-border rounded-xl hover:bg-muted disabled:opacity-40 disabled:cursor-not-allowed transition-all active:scale-95"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                >
                  Next
                </button>
                <button
                  className="px-4 py-2 text-sm font-bold bg-secondary border border-border rounded-xl hover:bg-muted disabled:opacity-40 disabled:cursor-not-allowed transition-all active:scale-95"
                  onClick={() => setPage(totalPages)}
                  disabled={page >= totalPages}
                >
                  Last
                </button>
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
