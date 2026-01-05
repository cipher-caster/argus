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

function TimeframeSelectorComponent({ selected, onChange }: TimeframeSelectorProps) {
  const [customOpen, setCustomOpen] = useState(false);

  // Check if selected is a favorite
  const isSelectedInFavorites = FAVORITES.some((f) => f.value === selected);

  return (
    <div className="timeframe-wrapper">
      {/* Quick favorites */}
      <div className="favorites-list">
        {FAVORITES.map((tf) => (
          <button key={tf.value} className={`timeframe-btn ${selected === tf.value ? "active" : ""}`} onClick={() => onChange(tf.value)}>
            {tf.label}
          </button>
        ))}
      </div>

      {/* Dropdown for others */}
      <Dropdown
        trigger={
          <button className={`timeframe-btn ${!isSelectedInFavorites ? "active" : ""}`}>
            <ChevronDown size={14} />
            {!isSelectedInFavorites && <span>{selected}</span>}
          </button>
        }
      >
        <div className="interval-menu">
          {ALL_INTERVALS.map((group) => (
            <div key={group.label} className="interval-group">
              <div className="group-label">{group.label}</div>
              {group.items.map((item) => (
                <DropdownItem key={item.value} active={selected === item.value} onClick={() => onChange(item.value)}>
                  <span style={{ width: 24, display: "inline-block" }}>{item.value}</span>
                  {item.label}
                </DropdownItem>
              ))}
            </div>
          ))}

          <div className="custom-interval">
            <div className="group-label">Custom</div>
            <div className="custom-input-row">
              <input type="number" placeholder="1" className="custom-input" min="1" max="59" />
              <select className="custom-select">
                <option value="m">min</option>
                <option value="h">hour</option>
                <option value="d">day</option>
              </select>
              <button className="add-btn">Add</button>
            </div>
          </div>
        </div>
      </Dropdown>

      <style jsx>{`
        .timeframe-wrapper {
          display: flex;
          align-items: center;
          gap: 0px;
        }

        .favorites-list {
          display: flex;
          gap: 0px;
        }

        .timeframe-btn {
          height: 32px;
          min-width: 32px;
          padding: 0 8px;
          font-size: 14px;
          font-weight: 500;
          color: var(--text-muted);
          background: transparent;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          transition: all 0.1s;
          display: flex;
          justify-content: center;
          align-items: center;
          gap: 4px;
        }

        .timeframe-btn:hover:not(.active) {
          color: var(--accent-primary);
          background: var(--bg-tertiary);
        }

        .timeframe-btn.active {
          color: var(--accent-primary);
          font-weight: 700;
          background: transparent;
        }

        .interval-menu {
          width: 200px;
          max-height: 400px;
          overflow-y: auto;
          padding: 4px 0;
          background: var(--bg-secondary);
          border-radius: 4px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
          border: 1px solid var(--border-color);
        }

        .interval-group {
          margin-bottom: 4px;
        }

        .group-label {
          padding: 6px 14px 4px;
          font-size: 11px;
          color: var(--text-muted);
          font-weight: 600;
          text-transform: uppercase;
        }

        .custom-interval {
          padding: 8px 12px;
          border-top: 1px solid var(--border-color);
        }

        .custom-input-row {
          display: flex;
          gap: 4px;
        }

        .custom-input,
        .custom-select {
          background: var(--bg-tertiary);
          border: 1px solid var(--border-color);
          color: var(--text-primary);
          border-radius: 4px;
          padding: 4px;
          font-size: 12px;
        }

        .custom-input {
          width: 44px;
        }

        .add-btn {
          background: var(--accent-primary);
          color: white;
          border: none;
          border-radius: 4px;
          padding: 2px 12px;
          font-size: 12px;
          cursor: pointer;
        }
      `}</style>
    </div>
  );
}

export const TimeframeSelector = memo(TimeframeSelectorComponent);
