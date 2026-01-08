"use client";

import { Dropdown, DropdownItem } from "@/components/ui/Dropdown";
import { ChevronDown } from "lucide-react";
import { memo, useState } from "react";

interface TimeframeSelectorProps {
  selected: string;
  onChange: (timeframe: string) => void;
}

const FAVORITES = [
  { value: "15m", label: "15m" },
  { value: "1h", label: "1H" },
  { value: "4h", label: "4H" },
  { value: "1d", label: "1D" },
  { value: "1w", label: "1W" },
];

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

function TimeframeSelectorComponent({ selected, onChange }: TimeframeSelectorProps) {
  // Check if selected is a favorite
  const isSelectedInFavorites = FAVORITES.some((f) => f.value === selected);

  return (
    <div className="flex items-center gap-0.5">
      {/* Quick favorites */}
      <div className="flex items-center">
        {FAVORITES.map((tf) => (
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
                <DropdownItem key={item.value} active={selected === item.value} onClick={() => onChange(item.value)} className="flex items-center gap-3 px-3 py-2 text-sm font-medium hover:bg-muted cursor-pointer transition-colors">
                  <span className="w-6 font-bold text-muted-foreground/50">{item.value}</span>
                  <span className="text-foreground">{item.label}</span>
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
