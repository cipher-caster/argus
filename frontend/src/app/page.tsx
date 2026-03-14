"use client";

import { ActiveSetups } from "@/components/features/dashboard/ActiveSetups";
import { BTCCard } from "@/components/features/dashboard/BTCCard";
import { DashboardStatusBar } from "@/components/features/dashboard/DashboardStatusBar";
import { DashboardWatchlist } from "@/components/features/dashboard/DashboardWatchlist";
import { TopMovers } from "@/components/features/dashboard/TopMovers";
import { BarChart2, ChevronRight } from "lucide-react";
import Link from "next/link";

export default function Dashboard() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <main className="max-w-[1440px] mx-auto p-6 md:p-8 space-y-5">

        {/* Single status bar — Oracle state + RSI + Market Cap + BTC Dom */}
        <section className="animate-in fade-in slide-in-from-top-2 duration-500">
          <DashboardStatusBar />
        </section>

        {/* Main Grid: Active Setups + BTC Card + Watchlist */}
        <section className="grid grid-cols-1 lg:grid-cols-5 gap-5 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <div className="lg:col-span-3">
            <ActiveSetups />
          </div>
          <div className="lg:col-span-2 flex flex-col gap-5">
            <BTCCard />
            <DashboardWatchlist />
          </div>
        </section>

        {/* Top Movers */}
        <section className="animate-in fade-in slide-in-from-bottom-5 duration-700 delay-75">
          <TopMovers />
        </section>

        {/* Footer link */}
        <section className="flex justify-center pb-4 animate-in fade-in duration-700 delay-100">
          <Link
            href="/markets"
            className="flex items-center gap-2 text-xs font-bold text-muted-foreground hover:text-foreground transition-colors group"
          >
            <BarChart2 size={13} />
            View full market table
            <ChevronRight size={11} className="group-hover:translate-x-0.5 transition-transform" />
          </Link>
        </section>

      </main>
    </div>
  );
}
