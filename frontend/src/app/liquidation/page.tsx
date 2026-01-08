"use client";

/**
 * Liquidation Heatmap Page
 * Displays a CoinGlass-style liquidation heatmap for crypto futures
 */

import { LiquidationControls } from "@/components/LiquidationControls";
import { HeatmapLegend, LiquidationHeatmap } from "@/components/LiquidationHeatmap";
import { useLiquidationHeatmap, useLiquidationSymbols } from "@/hooks/useLiquidationData";
import { Flame } from "lucide-react";
import { useState } from "react";

export default function LiquidationPage() {
  const [symbol, setSymbol] = useState("BTCUSDT");
  const [lookbackHours, setLookbackHours] = useState(24);
  const [threshold, setThreshold] = useState(0);

  const { data: symbolsData } = useLiquidationSymbols();
  const { data, isLoading, isFetching, refetch } = useLiquidationHeatmap(symbol, lookbackHours);

  const symbols = symbolsData?.symbols || ["BTCUSDT"];

  return (
    <div className="min-h-screen bg-background text-foreground">
      <main className="max-w-[1440px] mx-auto p-6 md:p-8 space-y-6">
        {/* Header */}
        <header className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-gradient-to-br from-orange-500/20 to-red-500/20">
            <Flame className="w-6 h-6 text-orange-500" />
          </div>
          <div>
            <h1 className="text-2xl font-extrabold tracking-tight">Liquidation Heatmap</h1>
            <p className="text-sm text-muted-foreground">Real-time futures liquidation visualization from Binance</p>
          </div>
        </header>

        {/* Controls */}
        <LiquidationControls
          symbol={symbol}
          onSymbolChange={setSymbol}
          symbols={symbols}
          lookbackHours={lookbackHours}
          onLookbackChange={setLookbackHours}
          threshold={threshold}
          onThresholdChange={setThreshold}
          onRefresh={() => refetch()}
          isRefreshing={isFetching}
        />

        {/* Info Box */}
        <div className="flex items-center justify-between p-4 bg-secondary/30 rounded-xl border border-border/50">
          <div className="flex items-center gap-6 text-sm">
            <div>
              <span className="text-muted-foreground">Symbol: </span>
              <span className="font-bold">{symbol.replace("USDT", "/USDT")} Perpetual</span>
            </div>
            {data && (
              <>
                <div>
                  <span className="text-muted-foreground">Price Range: </span>
                  <span className="font-mono">
                    ${data.price_min.toLocaleString()} - ${data.price_max.toLocaleString()}
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground">Data Points: </span>
                  <span className="font-mono">{data.time_buckets.length}</span>
                </div>
              </>
            )}
          </div>
          <HeatmapLegend />
        </div>

        {/* Heatmap */}
        <section className="bg-secondary/30 rounded-2xl border border-border/50 overflow-hidden">
          <div className="h-[500px]">
            <LiquidationHeatmap data={data} isLoading={isLoading} threshold={threshold} />
          </div>
        </section>

        {/* Footer Note */}
        <p className="text-xs text-muted-foreground text-center">
          Data streams from Binance Futures WebSocket. Liquidation events are aggregated into 15-second time buckets and $50 price levels.
          {!data?.time_buckets.length && " Waiting for new liquidation events..."}
        </p>
      </main>
    </div>
  );
}
