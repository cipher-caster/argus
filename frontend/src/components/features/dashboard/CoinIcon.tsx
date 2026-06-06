"use client";

import { CoinMeta, getCoinImageUrl, getCoinName } from "@/hooks/useCoinMeta";
import { cn } from "@/lib/utils";
import { useState } from "react";

interface CoinIconProps {
  symbol: string;
  coinMeta?: Map<string, CoinMeta>;
  size?: number;
  className?: string;
  showFallback?: boolean;
}

export function CoinIcon({ symbol, coinMeta, size = 28, className, showFallback = true }: CoinIconProps) {
  const [error, setError] = useState(false);

  const imageUrl = coinMeta ? getCoinImageUrl(symbol, coinMeta) : null;
  const coinName = coinMeta ? getCoinName(symbol, coinMeta) : symbol;

  // Deterministic color based on symbol char code
  const getFallbackColor = (s: string) => {
    const colors = ["bg-blue-500", "bg-green-500", "bg-yellow-500", "bg-purple-500", "bg-pink-500", "bg-indigo-500", "bg-red-500", "bg-orange-500", "bg-teal-500"];
    const code = s.charCodeAt(0) + (s.charCodeAt(s.length - 1) || 0);
    return colors[code % colors.length];
  };

  if (imageUrl && !error) {
    return (
      /* eslint-disable-next-line @next/next/no-img-element */
      <img src={imageUrl} alt={coinName} width={size} height={size} className={cn("rounded-full bg-secondary shrink-0 object-cover", className)} style={{ width: size, height: size }} onError={() => setError(true)} />
    );
  }

  if (!showFallback) return null;

  const letter = (coinName || symbol).slice(0, 1).toUpperCase();
  const bgColor = getFallbackColor(symbol);

  return (
    <div className={cn("rounded-full text-white flex items-center justify-center font-extrabold shrink-0 select-none", bgColor, className)} style={{ width: size, height: size, fontSize: Math.max(10, size * 0.45) }}>
      {letter}
    </div>
  );
}
