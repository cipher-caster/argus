"use client";

import { Dropdown, DropdownItem } from "@/components/ui/Dropdown";
import { ChevronDown } from "lucide-react";
import { memo } from "react";

interface TimeframeSelectorProps {
  selected: string;
  onChange: (timeframe: string) => void;
}

const ALL_INTERVALS = [
  {
    label: "Minutes",
    items: [
      { value: "1m", label: "1 minute" },
      { value: "5m", label: "5 minutes" },
      { value: "15m", label: "15 minutes" },
      { value: "30m", label: "30 minutes" },
    ],
  },
  {
    label: "Hours",
    items: [
      { value: "1h", label: "1 hour" },
      { value: "4h", label: "4 hours" },
      { value: "12h", label: "12 hours" },
    ],
  },
  {
    label: "Days",
    items: [
      { value: "1d", label: "1 day" },
      { value: "3d", label: "3 days" },
      { value: "1w", label: "1 week" },
      { value: "1M", label: "1 month" },
    ],
  },
];

import { cn } from "@/lib/utils";

import { Star } from "lucide-react";
import { useEffect, useState } from "react";

function TimeframeSelectorComponent({ selected, onChange }: TimeframeSelectorProps) {
  // Default favorites
  const DEFAULT_FAVORITES = [
    { value: "15m", label: "15m" },
    { value: "1h", label: "1H" },
    { value: "4h", label: "4H" },
    { value: "12h", label: "12H" },
    { value: "1d", label: "1D" },
    { value: "3d", label: "3D" },
    { value: "1w", label: "1W" },
  ];

  const [favorites, setFavorites] = useState<{ value: string; label: string }[]>(DEFAULT_FAVORITES);
  const [mounted, setMounted] = useState(false);

  // Load from localStorage on mount
  useEffect(() => {
    setMounted(true);
    try {
      const saved = localStorage.getItem("argus_favorite_timeframes");
      if (saved) {
        setFavorites(JSON.parse(saved));
      }
    } catch (e) {
      if (process.env.NODE_ENV === "development") console.error("Failed to load favorite timeframes", e);
    }
  }, []);

  const toggleFavorite = (value: string, label: string, e: React.MouseEvent) => {
    e.stopPropagation();
    let newFavorites;
    if (favorites.some((f) => f.value === value)) {
      newFavorites = favorites.filter((f) => f.value !== value);
    } else {
      newFavorites = [...favorites, { value, label }].sort((a, b) => {
        // Simple sort order logic based on ALL_INTERVALS order would be better, but for now append/remove
        // To keep order correct, we might want to filter from a master list
        const aIndex = getAllIntervalsFlat().findIndex((i) => i.value === a.value);
        const bIndex = getAllIntervalsFlat().findIndex((i) => i.value === b.value);
        return aIndex - bIndex;
      });
    }
    setFavorites(newFavorites);
    localStorage.setItem("argus_favorite_timeframes", JSON.stringify(newFavorites));
  };

  const getAllIntervalsFlat = () => {
    return ALL_INTERVALS.flatMap((g) => g.items);
  };

  const isFavorite = (value: string) => favorites.some((f) => f.value === value);

  // Check if selected is a favorite
  const isSelectedInFavorites = isFavorite(selected);

  if (!mounted) return null;

  return (
    <div className="flex items-center gap-0.5">
      {/* Quick favorites */}
      <div className="flex items-center">
        {favorites.map((tf) => (
          <button
            key={tf.value}
            className={cn("h-8 px-2.5 text-[13px] font-bold transition-all duration-200 rounded-md", selected === tf.value ? "text-primary bg-primary/10 shadow-sm" : "text-muted-foreground hover:bg-muted hover:text-foreground")}
            onClick={() => onChange(tf.value)}
          >
            {tf.label}
          </button>
        ))}
      </div>

      {/* Dropdown for others */}
      <Dropdown
        trigger={
          <button className={cn("h-8 px-2 flex items-center gap-1 text-[13px] font-bold rounded-md transition-all", !isSelectedInFavorites ? "text-primary bg-primary/10" : "text-muted-foreground hover:bg-muted hover:text-foreground")}>
            <ChevronDown size={14} />
            {!isSelectedInFavorites && <span>{selected}</span>}
          </button>
        }
      >
        <div className="w-[220px] bg-card border border-border rounded-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200 py-1">
          {ALL_INTERVALS.map((group) => (
            <div key={group.label} className="py-1">
              <div className="px-3 py-1 text-[10px] font-extrabold text-muted-foreground uppercase tracking-wider">{group.label}</div>
              {group.items.map((item) => (
                <DropdownItem key={item.value} active={selected === item.value} onClick={() => onChange(item.value)} className="flex items-center justify-between px-3 py-2 text-sm font-medium hover:bg-muted cursor-pointer transition-colors group">
                  <div className="flex items-center gap-3">
                    <span className="w-8 font-bold text-muted-foreground/50">{item.value}</span>
                    <span className="text-foreground">{item.label}</span>
                  </div>
                  <button
                    onClick={(e) => toggleFavorite(item.value, item.value.toUpperCase(), e)}
                    className={cn("p-1 rounded-md hover:bg-background transition-colors", isFavorite(item.value) ? "text-yellow-400" : "text-muted-foreground/30 opacity-0 group-hover:opacity-100")}
                  >
                    <Star size={14} fill={isFavorite(item.value) ? "currentColor" : "none"} />
                  </button>
                </DropdownItem>
              ))}
            </div>
          ))}

          <div className="mt-1 border-t border-border pt-2 px-3 pb-2">
            <div className="text-[10px] font-extrabold text-muted-foreground uppercase tracking-wider mb-2">Custom</div>
            <div className="flex gap-1.5">
              <input type="number" placeholder="1" className="w-12 h-8 bg-secondary border border-border rounded-lg px-2 text-xs focus:ring-1 focus:ring-primary/30 outline-none" min="1" max="59" />
              <select className="flex-1 h-8 bg-secondary border border-border rounded-lg px-1.5 text-xs focus:ring-1 focus:ring-primary/30 outline-none cursor-pointer">
                <option value="m">min</option>
                <option value="h">hour</option>
                <option value="d">day</option>
              </select>
              <button className="h-8 px-3 bg-primary text-primary-foreground text-[11px] font-bold rounded-lg hover:bg-primary/90 transition-all shadow-sm">Add</button>
            </div>
          </div>
        </div>
      </Dropdown>
    </div>
  );
}

export const TimeframeSelector = memo(TimeframeSelectorComponent);
