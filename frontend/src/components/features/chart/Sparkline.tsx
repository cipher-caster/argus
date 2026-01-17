"use client";

import { useMemo } from "react";

interface SparklineProps {
  data: number[];
  width?: number | string;
  height?: number;
  color?: string;
}

/**
 * Lightweight SVG Sparkline component
 * Renders a trend line based on an array of numbers
 */
export function Sparkline({ data, width = 100, height = 30, color }: SparklineProps) {
  // Use fixed coordinate system (0-100) for path calculation to allow SVG scaling
  const internalWidth = 100;

  const points = useMemo(() => {
    if (!data || data.length < 2) return "";

    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;

    return data
      .map((val, i) => {
        const x = (i / (data.length - 1)) * internalWidth;
        const y = height - ((val - min) / range) * height;
        return `${x},${y}`;
      })
      .join(" ");
  }, [data, height]);

  // Determine color based on trend if not provided
  const trendColor = useMemo(() => {
    if (color) return color;
    if (!data || data.length < 2) return "var(--text-muted)";
    return data[data.length - 1] >= data[0] ? "hsl(var(--success))" : "hsl(var(--danger))";
  }, [data, color]);

  if (!data || data.length < 2) {
    return (
      <div style={{ width: width || "100%", height, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ width: "80%", height: 1, background: "var(--border-color)", opacity: 0.5 }} />
      </div>
    );
  }

  return (
    <svg width={width || "100%"} height={height} viewBox={`0 0 ${internalWidth} ${height}`} preserveAspectRatio="none" className="block w-full">
      <path d={`M ${points}`} fill="none" stroke={trendColor} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
