import { create } from "zustand";
import { persist } from "zustand/middleware";

interface WatchlistItem {
  symbol: string;
  addedAt: number;
}

interface WatchlistStore {
  items: WatchlistItem[];
  addSymbol: (symbol: string) => void;
  removeSymbol: (symbol: string) => void;
  hasSymbol: (symbol: string) => boolean;
  setItems: (items: WatchlistItem[]) => void;
}

export const useWatchlistStore = create<WatchlistStore>()(
  persist(
    (set, get) => ({
      items: [
        { symbol: "BTC/USDT", addedAt: Date.now() },
        { symbol: "ETH/USDT", addedAt: Date.now() },
        { symbol: "SOL/USDT", addedAt: Date.now() },
      ],

      addSymbol: (symbol: string) => {
        const { items } = get();
        if (items.find((item) => item.symbol === symbol)) return;
        set({ items: [...items, { symbol, addedAt: Date.now() }] });
      },

      removeSymbol: (symbol: string) => {
        set({ items: get().items.filter((item) => item.symbol !== symbol) });
      },

      hasSymbol: (symbol: string) => {
        return !!get().items.find((item) => item.symbol === symbol);
      },
      setItems: (items: WatchlistItem[]) => {
        set({ items });
      },
    }),
    {
      name: "argus-watchlist",
    }
  )
);
