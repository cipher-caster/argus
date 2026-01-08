"use client";

/**
 * LiquidationHeatmap - Canvas-based heatmap visualization
 * Shows liquidation intensity by price level over time
 */

import { LiquidationHeatmapResponse } from "@/lib/api";
import { useCallback, useEffect, useRef, useState } from "react";

interface LiquidationHeatmapProps {
  data: LiquidationHeatmapResponse | undefined;
  isLoading: boolean;
  threshold: number; // 0-1, filters out low intensity cells
}

// Color gradient: dark blue -> cyan -> green -> yellow (like CoinGlass)
const GRADIENT_COLORS = [
  { pos: 0.0, r: 30, g: 30, b: 80 }, // Deep blue
  { pos: 0.2, r: 0, g: 80, b: 120 }, // Dark cyan
  { pos: 0.4, r: 0, g: 140, b: 140 }, // Cyan
  { pos: 0.6, r: 0, g: 180, b: 80 }, // Green
  { pos: 0.8, r: 180, g: 200, b: 0 }, // Yellow-green
  { pos: 1.0, r: 255, g: 255, b: 0 }, // Bright yellow
];

function interpolateColor(intensity: number): string {
  const clamped = Math.max(0, Math.min(1, intensity));

  // Find the two colors to interpolate between
  let lower = GRADIENT_COLORS[0];
  let upper = GRADIENT_COLORS[GRADIENT_COLORS.length - 1];

  for (let i = 0; i < GRADIENT_COLORS.length - 1; i++) {
    if (clamped >= GRADIENT_COLORS[i].pos && clamped <= GRADIENT_COLORS[i + 1].pos) {
      lower = GRADIENT_COLORS[i];
      upper = GRADIENT_COLORS[i + 1];
      break;
    }
  }

  const range = upper.pos - lower.pos;
  const t = range > 0 ? (clamped - lower.pos) / range : 0;

  const r = Math.round(lower.r + t * (upper.r - lower.r));
  const g = Math.round(lower.g + t * (upper.g - lower.g));
  const b = Math.round(lower.b + t * (upper.b - lower.b));

  return `rgb(${r}, ${g}, ${b})`;
}

export function LiquidationHeatmap({ data, isLoading, threshold }: LiquidationHeatmapProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 500 });

  // Handle resize
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const observer = new ResizeObserver((entries) => {
      const { width, height } = entries[0].contentRect;
      setDimensions({ width: Math.floor(width), height: Math.floor(height) });
    });

    observer.observe(container);
    return () => observer.disconnect();
  }, []);

  // Draw heatmap
  const drawHeatmap = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !data) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const { width, height } = dimensions;
    const padding = { top: 20, right: 60, bottom: 40, left: 10 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;

    // Clear canvas
    ctx.fillStyle = "#0a0a14";
    ctx.fillRect(0, 0, width, height);

    if (data.time_buckets.length === 0) {
      ctx.fillStyle = "#888";
      ctx.font = "14px Inter, sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("Waiting for liquidation data...", width / 2, height / 2);
      return;
    }

    // Calculate scales
    const timeMin = Math.min(...data.time_buckets.map((b) => b.timestamp));
    const timeMax = Math.max(...data.time_buckets.map((b) => b.timestamp));
    const timeRange = Math.max(timeMax - timeMin, 60); // Minimum 1 minute range

    // Ensure reasonable price range (at least $1000 around the data)
    const priceBucketSize = 50; // Match backend
    const dataPriceMin = data.price_min;
    const dataPriceMax = data.price_max;
    const priceCenter = (dataPriceMin + dataPriceMax) / 2;
    const minPriceRange = 2000; // At least $2000 range
    const actualPriceRange = dataPriceMax - dataPriceMin;

    let priceMin = dataPriceMin;
    let priceMax = dataPriceMax;
    if (actualPriceRange < minPriceRange) {
      priceMin = priceCenter - minPriceRange / 2;
      priceMax = priceCenter + minPriceRange / 2;
    }
    const priceRange = priceMax - priceMin;

    // Fixed cell dimensions (not relative to data count)
    const cellWidth = Math.min(Math.max(4, chartWidth / 200), 20); // 4-20px wide
    const cellHeight = Math.max(4, (priceBucketSize / priceRange) * chartHeight); // At least 4px tall

    data.time_buckets.forEach((bucket) => {
      const x = padding.left + ((bucket.timestamp - timeMin) / timeRange) * chartWidth;

      Object.entries(bucket.price_buckets).forEach(([priceStr, volume]) => {
        const price = parseFloat(priceStr);
        const intensity = data.max_intensity > 0 ? volume / data.max_intensity : 0;

        // Apply threshold filter
        if (intensity < threshold) return;

        const y = padding.top + ((priceMax - price) / priceRange) * chartHeight;

        ctx.fillStyle = interpolateColor(intensity);
        ctx.fillRect(x - cellWidth / 2, y - cellHeight / 2, cellWidth, Math.max(cellHeight, 4));
      });
    });

    // Draw OHLCV overlay (candlestick line)
    if (data.ohlcv.length > 0) {
      ctx.strokeStyle = "rgba(255, 255, 255, 0.8)";
      ctx.lineWidth = 2;
      ctx.beginPath();

      data.ohlcv.forEach((candle, i) => {
        const x = padding.left + ((candle.timestamp - timeMin) / timeRange) * chartWidth;
        const y = padding.top + ((priceMax - candle.close) / priceRange) * chartHeight;

        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });

      ctx.stroke();
    }

    // Draw Y-axis (price levels)
    ctx.fillStyle = "#888";
    ctx.font = "11px Inter, sans-serif";
    ctx.textAlign = "right";

    const priceSteps = 6;
    for (let i = 0; i <= priceSteps; i++) {
      const price = priceMin + (priceRange * i) / priceSteps;
      const y = padding.top + chartHeight - (i / priceSteps) * chartHeight;

      ctx.fillText(price.toLocaleString(undefined, { maximumFractionDigits: 0 }), width - 5, y + 4);

      // Grid line
      ctx.strokeStyle = "rgba(255, 255, 255, 0.1)";
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(width - padding.right, y);
      ctx.stroke();
    }

    // Draw X-axis (time labels)
    ctx.textAlign = "center";
    const timeSteps = Math.min(8, data.time_buckets.length);
    const stepSize = Math.floor(data.time_buckets.length / timeSteps);

    for (let i = 0; i < data.time_buckets.length; i += stepSize) {
      const bucket = data.time_buckets[i];
      const x = padding.left + ((bucket.timestamp - timeMin) / timeRange) * chartWidth;
      const date = new Date(bucket.timestamp * 1000);
      const label = date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

      ctx.fillText(label, x, height - 10);
    }
  }, [data, dimensions, threshold]);

  useEffect(() => {
    drawHeatmap();
  }, [drawHeatmap]);

  return (
    <div ref={containerRef} className="w-full h-full min-h-[400px] relative">
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-background/50 z-10">
          <div className="flex items-center gap-2 text-muted-foreground">
            <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            Loading...
          </div>
        </div>
      )}
      <canvas ref={canvasRef} width={dimensions.width} height={dimensions.height} className="w-full h-full" />
    </div>
  );
}

/**
 * Color legend component
 */
export function HeatmapLegend() {
  return (
    <div className="flex items-center gap-2 text-xs text-muted-foreground">
      <span>Low</span>
      <div
        className="w-32 h-3 rounded-sm"
        style={{
          background: "linear-gradient(to right, rgb(30,30,80), rgb(0,80,120), rgb(0,140,140), rgb(0,180,80), rgb(180,200,0), rgb(255,255,0))",
        }}
      />
      <span>High</span>
    </div>
  );
}
