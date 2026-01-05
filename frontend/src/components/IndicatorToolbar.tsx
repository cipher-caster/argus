"use client";

/**
 * Indicator Toolbar Component
 * TradingView-style vertical toolbar for managing indicators
 */

import { IndicatorConfig, useIndicatorStore } from "@/stores/indicatorStore";
import { Edit2, Plus, Trash2 } from "lucide-react";
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
          <Plus size={20} />
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
                <Edit2 size={16} />
              </button>
              <button className="action-btn delete-btn" onClick={() => removeIndicator(ind.id)} title="Remove">
                <Trash2 size={16} />
              </button>
            </div>
          </div>
        ))}

        <style jsx>{`
          .indicator-toolbar {
            display: flex;
            flex-direction: column;
            gap: 8px;
            padding: 12px;
            background: var(--bg-secondary);
            border-radius: 12px;
            border: 1px solid var(--border-color);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
          }

          .toolbar-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 44px;
            height: 44px;
            background: transparent;
            border: none;
            border-radius: 10px;
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
          }

          .toolbar-btn:hover {
            background: var(--bg-tertiary);
            color: var(--text-primary);
            transform: translateY(-1px);
          }

          .toolbar-btn:active {
            transform: translateY(0);
          }

          .add-btn {
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
            color: var(--accent-primary);
            border: 1px solid rgba(99, 102, 241, 0.2);
          }

          .add-btn:hover {
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(139, 92, 246, 0.2) 100%);
            color: var(--accent-secondary);
            border-color: rgba(99, 102, 241, 0.4);
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
          }

          .toolbar-divider {
            height: 1px;
            background: var(--border-color);
            margin: 4px 0;
            opacity: 0.5;
          }

          .indicator-item {
            position: relative;
          }

          .indicator-btn {
            border-left: 3px solid;
            border-radius: 4px 10px 10px 4px;
            padding-left: 8px;
            width: 100%;
            justify-content: flex-start;
          }

          .indicator-btn.hidden-indicator {
            opacity: 0.5;
            filter: grayscale(0.8);
          }

          .indicator-label {
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.5px;
          }

          .indicator-actions {
            position: absolute;
            left: calc(100% + 8px);
            top: 0;
            display: none;
            flex-direction: row;
            gap: 4px;
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 4px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 10;
            animation: fadeIn 0.15s ease-out;
          }

          .indicator-item:hover .indicator-actions {
            display: flex;
          }

          .action-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 32px;
            height: 32px;
            background: transparent;
            border: none;
            border-radius: 6px;
            color: var(--text-muted);
            cursor: pointer;
            transition: all 0.15s ease;
          }

          .action-btn:hover {
            background: var(--bg-secondary);
            color: var(--text-primary);
          }

          .action-btn.delete-btn:hover {
            background: rgba(239, 68, 68, 0.15);
            color: var(--danger);
          }

          @keyframes fadeIn {
            from {
              opacity: 0;
              transform: translateX(-5px);
            }
            to {
              opacity: 1;
              transform: translateX(0);
            }
          }
        `}</style>
      </div>

      <IndicatorModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} editingIndicator={editingIndicator} />
    </>
  );
}

export const IndicatorToolbar = memo(IndicatorToolbarComponent);
