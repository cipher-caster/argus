"use client";

/**
 * Timeframe Selector Component
 */

import { memo } from "react";

interface TimeframeSelectorProps {
  selected: string;
  onChange: (timeframe: string) => void;
}

const TIMEFRAMES = [
  { value: "1h", label: "1H" },
  { value: "4h", label: "4H" },
  { value: "1d", label: "1D" },
  { value: "1w", label: "1W" },
];

function TimeframeSelectorComponent({ selected, onChange }: TimeframeSelectorProps) {
  return (
    <div className="timeframe-selector">
      {TIMEFRAMES.map((tf) => (
        <button key={tf.value} className={`timeframe-btn ${selected === tf.value ? "active" : ""}`} onClick={() => onChange(tf.value)}>
          {tf.label}
        </button>
      ))}

      <style jsx>{`
        .timeframe-selector {
          display: flex;
          gap: 4px;
          padding: 4px;
          background: #12121a;
          border-radius: 8px;
          border: 1px solid #1a1a2e;
        }

        .timeframe-btn {
          padding: 8px 16px;
          font-size: 13px;
          font-weight: 500;
          color: #a0a0b0;
          background: transparent;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .timeframe-btn:hover {
          color: #ffffff;
          background: #1a1a2e;
        }

        .timeframe-btn.active {
          color: #ffffff;
          background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
          box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
        }
      `}</style>
    </div>
  );
}

export const TimeframeSelector = memo(TimeframeSelectorComponent);
