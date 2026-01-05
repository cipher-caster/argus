"use client";

/**
 * Indicator Toolbar Component
 * TradingView-style vertical toolbar for managing indicators
 */

import { IndicatorConfig, useIndicatorStore } from "@/stores/indicatorStore";
import { memo, useState } from "react";
import { IndicatorModal } from "./IndicatorModal";

function IndicatorToolbarComponent() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingIndicator, setEditingIndicator] = useState<IndicatorConfig | null>(null);

  const indicators = useIndicatorStore((s) => s.indicators);
  const toggleVisibility = useIndicatorStore((s) => s.toggleVisibility);
  const removeIndicator = useIndicatorStore((s) => s.removeIndicator);

  const handleEdit = (indicator: IndicatorConfig) => {
    setEditingIndicator(indicator);
    setIsModalOpen(true);
  };

  const handleAdd = () => {
    setEditingIndicator(null);
    setIsModalOpen(true);
  };

  return (
    <>
      <div className="indicator-toolbar">
        {/* Add Indicator Button */}
        <button className="toolbar-btn add-btn" onClick={handleAdd} title="Add Indicator">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            <path d="M12 5v14M5 12h14" />
          </svg>
        </button>

        <div className="toolbar-divider" />

        {/* Active Indicators */}
        {indicators.map((ind) => (
          <div key={ind.id} className="indicator-item">
            <button className={`toolbar-btn indicator-btn ${!ind.visible ? "hidden-indicator" : ""}`} onClick={() => toggleVisibility(ind.id)} title={ind.displayName} style={{ borderLeftColor: ind.color }}>
              <span className="indicator-label">{ind.type.toUpperCase()}</span>
            </button>
            <div className="indicator-actions">
              <button className="action-btn" onClick={() => handleEdit(ind)} title="Edit">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                  <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
                  <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
                </svg>
              </button>
              <button className="action-btn delete-btn" onClick={() => removeIndicator(ind.id)} title="Remove">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                  <path d="M18 6L6 18M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        ))}

        <style jsx>{`
          .indicator-toolbar {
            display: flex;
            flex-direction: column;
            gap: 4px;
            padding: 8px;
            background: var(--bg-secondary);
            border-radius: 10px;
            border: 1px solid var(--border-color);
          }

          .toolbar-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 40px;
            height: 40px;
            background: transparent;
            border: none;
            border-radius: 8px;
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.2s ease;
          }

          .toolbar-btn:hover {
            background: var(--bg-tertiary);
            color: var(--text-primary);
          }

          .toolbar-btn svg {
            width: 20px;
            height: 20px;
          }

          .add-btn {
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(139, 92, 246, 0.2) 100%);
            color: var(--accent-primary);
          }

          .add-btn:hover {
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.4) 0%, rgba(139, 92, 246, 0.4) 100%);
            color: var(--accent-secondary);
          }

          .toolbar-divider {
            height: 1px;
            background: var(--border-color);
            margin: 4px 0;
          }

          .indicator-item {
            position: relative;
          }

          .indicator-btn {
            border-left: 3px solid;
            border-radius: 0 8px 8px 0;
            padding-left: 8px;
          }

          .indicator-btn.hidden-indicator {
            opacity: 0.4;
          }

          .indicator-label {
            font-size: 10px;
            font-weight: 600;
            letter-spacing: 0.5px;
          }

          .indicator-actions {
            position: absolute;
            left: 100%;
            top: 0;
            display: none;
            flex-direction: row;
            gap: 2px;
            margin-left: 4px;
            background: var(--bg-tertiary);
            border-radius: 6px;
            padding: 4px;
          }

          .indicator-item:hover .indicator-actions {
            display: flex;
          }

          .action-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 28px;
            height: 28px;
            background: transparent;
            border: none;
            border-radius: 4px;
            color: var(--text-muted);
            cursor: pointer;
            transition: all 0.15s ease;
          }

          .action-btn:hover {
            background: var(--bg-secondary);
            color: var(--text-primary);
          }

          .action-btn.delete-btn:hover {
            background: rgba(239, 68, 68, 0.2);
            color: var(--danger);
          }

          .action-btn svg {
            width: 14px;
            height: 14px;
          }
        `}</style>
      </div>

      <IndicatorModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} editingIndicator={editingIndicator} />
    </>
  );
}

export const IndicatorToolbar = memo(IndicatorToolbarComponent);
