"use client";

import { BTCCard } from "@/components/features/dashboard/BTCCard";
import { DashboardStatusBar } from "@/components/features/dashboard/DashboardStatusBar";
import { DashboardWatchlist } from "@/components/features/dashboard/DashboardWatchlist";
import { ActiveSetups } from "@/components/features/dashboard/ActiveSetups";
import { ActiveSignals } from "@/components/features/dashboard/ActiveSignals";
import { TopMovers } from "@/components/features/dashboard/TopMovers";
import { TradingWidget } from "@/components/features/dashboard/TradingWidget";

export default function Dashboard() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <main className="max-w-[1440px] mx-auto p-6 md:p-8 space-y-5">

        {/* Status bar — regime + market indicators + clickable modal */}
        <section className="animate-in fade-in slide-in-from-top-2 duration-500">
          <DashboardStatusBar />
        </section>

        {/* Main Grid: Best Setups + BTC Card + Watchlist */}
        <section className="grid grid-cols-1 lg:grid-cols-5 gap-5 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <div className="lg:col-span-3">
            <ActiveSetups />
          </div>
          <div className="lg:col-span-2 flex flex-col gap-5">
            <BTCCard />
            <DashboardWatchlist />
          </div>
        </section>

        {/* Active Signals (60%) + Trading Widget (40%) */}
        <section className="grid grid-cols-1 lg:grid-cols-5 gap-5 items-stretch animate-in fade-in slide-in-from-bottom-4 duration-700 delay-75">
          <div className="lg:col-span-3 flex">
            <ActiveSignals />
          </div>
          <div className="lg:col-span-2 flex">
            <TradingWidget />
          </div>
        </section>

        {/* Top Movers */}
        <section className="animate-in fade-in slide-in-from-bottom-3 duration-600 delay-100">
          <TopMovers />
        </section>

      </main>
    </div>
  );
}
