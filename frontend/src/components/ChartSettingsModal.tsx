"use client";

import { ChartColorSettings, useChartSettingsStore } from "@/stores/chartSettingsStore";
import { themes, useThemeStore } from "@/stores/themeStore";
import { RotateCcw, X } from "lucide-react";
import { memo, useEffect, useState } from "react";
import { createPortal } from "react-dom";

interface ChartSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

function ChartSettingsModalComponent({ isOpen, onClose }: ChartSettingsModalProps) {
  const { colors, setColors, resetColors } = useChartSettingsStore();
  const theme = useThemeStore((s) => s.theme);
  const currentTheme = themes[theme];

  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted || !isOpen) return null;

  const handleColorChange = (key: keyof ChartColorSettings, value: string) => {
    setColors({ [key]: value });
  };

  const ColorInput = ({ label, keyName, fallback }: { label: string; keyName: keyof ChartColorSettings; fallback: string }) => (
    <div className="setting-row">
      <label>{label}</label>
      <div className="color-input-wrapper">
        <input type="color" value={colors[keyName] || fallback} onChange={(e) => handleColorChange(keyName, e.target.value)} className="color-input" />
        <span className="color-value">{colors[keyName] || "Auto"}</span>
        {colors[keyName] && (
          <button className="reset-field-btn" onClick={() => handleColorChange(keyName, "")} title="Reset to auto">
            <X size={12} />
          </button>
        )}
      </div>
    </div>
  );

  return (
    <>
      {createPortal(
        <div className="modal-overlay" onClick={onClose}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Chart Settings</h2>
              <button className="close-btn" onClick={onClose}>
                <X size={20} />
              </button>
            </div>

            <div className="modal-body">
              <div className="settings-section">
                <h3>Candlesticks</h3>

                <div className="settings-grid">
                  <div className="column">
                    <h4>Up Candle (Bullish)</h4>
                    <ColorInput label="Body" keyName="upColor" fallback={currentTheme.positive} />
                    <ColorInput label="Borders" keyName="borderUpColor" fallback={currentTheme.positive} />
                    <ColorInput label="Wick" keyName="wickUpColor" fallback={currentTheme.positive} />
                  </div>

                  <div className="column">
                    <h4>Down Candle (Bearish)</h4>
                    <ColorInput label="Body" keyName="downColor" fallback={currentTheme.negative} />
                    <ColorInput label="Borders" keyName="borderDownColor" fallback={currentTheme.negative} />
                    <ColorInput label="Wick" keyName="wickDownColor" fallback={currentTheme.negative} />
                  </div>
                </div>
              </div>
            </div>

            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={resetColors}>
                <RotateCcw size={14} />
                Reset Defaults
              </button>
              <button className="btn btn-primary" onClick={onClose}>
                Done
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}

      <style jsx global>{`
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 9999;
          backdrop-filter: blur(2px);
          animation: fadeIn 0.15s ease;
        }

        .modal-content {
          width: 100%;
          max-width: 450px;
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 12px;
          box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
          overflow: hidden;
          animation: slideUp 0.2s ease;
        }

        .modal-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 16px 20px;
          border-bottom: 1px solid var(--border-color);
          background: var(--bg-secondary);
        }

        .modal-header h2 {
          font-size: 16px;
          font-weight: 600;
          color: var(--text-primary);
          margin: 0;
        }

        .close-btn {
          background: transparent;
          border: none;
          color: var(--text-secondary);
          cursor: pointer;
          padding: 4px;
          border-radius: 4px;
        }

        .close-btn:hover {
          background: var(--bg-tertiary);
          color: var(--text-primary);
        }

        .modal-body {
          padding: 20px;
          background: var(--bg-primary);
        }

        .settings-section h3 {
          font-size: 14px;
          font-weight: 600;
          color: var(--text-muted);
          margin: 0 0 16px 0;
          text-transform: uppercase;
        }

        .settings-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 24px;
        }

        .column h4 {
          font-size: 13px;
          font-weight: 500;
          color: var(--text-primary);
          margin: 0 0 12px 0;
          padding-bottom: 8px;
          border-bottom: 1px solid var(--border-color);
        }

        .setting-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 12px;
        }

        .setting-row label {
          font-size: 13px;
          color: var(--text-secondary);
        }

        .color-input-wrapper {
          display: flex;
          align-items: center;
          gap: 8px;
          background: var(--bg-tertiary);
          padding: 4px;
          border-radius: 6px;
          border: 1px solid var(--border-color);
        }

        .color-input {
          width: 24px;
          height: 24px;
          padding: 0;
          border: none;
          background: none;
          cursor: pointer;
        }

        .color-value {
          font-size: 11px;
          font-family: monospace;
          color: var(--text-primary);
          min-width: 50px;
        }

        .reset-field-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          background: transparent;
          border: none;
          color: var(--text-muted);
          cursor: pointer;
          padding: 2px;
        }

        .reset-field-btn:hover {
          color: var(--text-primary);
        }

        .modal-footer {
          padding: 16px 20px;
          border-top: 1px solid var(--border-color);
          background: var(--bg-secondary);
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .btn {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 8px 16px;
          border-radius: 6px;
          font-size: 13px;
          font-weight: 500;
          border: none;
          cursor: pointer;
        }

        .btn-secondary {
          background: transparent;
          color: var(--text-secondary);
          border: 1px solid var(--border-color);
        }

        .btn-secondary:hover {
          background: var(--bg-tertiary);
          color: var(--text-primary);
        }

        .btn-primary {
          background: var(--accent-primary);
          color: white;
        }

        .btn-primary:hover {
          background: var(--accent-secondary);
        }

        @keyframes fadeIn {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }

        @keyframes slideUp {
          from {
            transform: translateY(20px);
            opacity: 0;
          }
          to {
            transform: translateY(0);
            opacity: 1;
          }
        }
      `}</style>
    </>
  );
}

export const ChartSettingsModal = memo(ChartSettingsModalComponent);
