"use client";

import { IndicatorConfig, useIndicatorStore } from "@/stores/indicatorStore";
import { BarChart2, CandlestickChart as CandleIcon, ChevronDown, Edit2, Eye, EyeOff, PlusCircle, Search, Trash2, X } from "lucide-react";
import { TimeframeSelector } from "../TimeframeSelector";
import { Dropdown } from "../ui/Dropdown";

interface ChartHeaderProps {
  symbol: string;
  isLoading?: boolean;
  timeframe?: string;
  onTimeframeChange?: (tf: string) => void;
  indicatorConfigs: IndicatorConfig[];
  onAddIndicator: () => void;
  onEditIndicator: (indicator: IndicatorConfig) => void;
}

export function ChartHeader({ symbol, isLoading, timeframe, onTimeframeChange, indicatorConfigs, onAddIndicator, onEditIndicator }: ChartHeaderProps) {
  const toggleVisibility = useIndicatorStore((s) => s.toggleVisibility);
  const removeIndicator = useIndicatorStore((s) => s.removeIndicator);

  const overlayIndicators = indicatorConfigs.filter((i) => i.visible && i.indicatorType === "overlay");

  return (
    <>
      <div className="chart-header">
        {/* Symbol Section */}
        <div className="header-group symbol-group">
          <Search size={18} style={{ color: "var(--text-muted)", cursor: "pointer" }} />
          <span className="chart-symbol">{symbol}</span>
          <div className="provider-badge-small">
            <div className="diamond-icon"></div>
          </div>
        </div>

        <div className="header-separator"></div>

        {/* Comparison */}
        <button className="icon-btn-circle" title="Compare or Add Symbol">
          <PlusCircle size={18} />
        </button>

        <div className="header-separator"></div>

        {/* Timeframes */}
        <div className="header-group timeframe-group">{timeframe && onTimeframeChange && <TimeframeSelector selected={timeframe} onChange={onTimeframeChange} />}</div>

        <div className="header-separator"></div>

        {/* Chart Type */}
        <div className="header-group">
          <button className="icon-btn" title="Chart Style">
            <CandleIcon size={20} />
          </button>
        </div>

        <div className="header-separator"></div>

        {/* Indicators */}
        <div className="header-group">
          <div className="indicators-button-group">
            <button className="text-icon-btn main-btn" onClick={onAddIndicator}>
              <BarChart2 size={18} />
              <span>Indicators</span>
            </button>
            <Dropdown
              trigger={
                <button className="dropdown-arrow-btn">
                  <ChevronDown size={14} />
                </button>
              }
            >
              <div className="active-indicators-menu">
                <div className="menu-header">Active Indicators</div>
                {indicatorConfigs.length === 0 ? (
                  <div className="no-indicators">No indicators added</div>
                ) : (
                  indicatorConfigs.map((ind) => (
                    <div key={ind.id} className="indicator-menu-item">
                      <div className="indicator-info">
                        <div className="color-dot" style={{ background: ind.color }}></div>
                        <span className="display-name">{ind.displayName}</span>
                      </div>
                      <div className="indicator-menu-actions">
                        <button onClick={() => toggleVisibility(ind.id)}>{ind.visible ? <Eye size={14} /> : <EyeOff size={14} />}</button>
                        <button onClick={() => onEditIndicator(ind)}>
                          <Edit2 size={14} />
                        </button>
                        <button onClick={() => removeIndicator(ind.id)} className="delete">
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </Dropdown>
          </div>
          {overlayIndicators.length > 0 && (
            <div className="indicator-badges">
              {overlayIndicators.map((i) => (
                <span key={i.id} className="indicator-badge interactable" style={{ borderColor: i.color, color: i.color }} onClick={() => onEditIndicator(i)}>
                  {i.displayName}
                  <button
                    className="indicator-remove-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      removeIndicator(i.id);
                    }}
                  >
                    <X size={10} />
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        {isLoading && <span className="chart-loading">Loading...</span>}
      </div>

      <style jsx global>{`
        .chart-header {
          display: flex;
          align-items: center;
          height: 38px;
          padding: 0 12px;
          background: var(--bg-secondary);
          border-bottom: 1px solid var(--border-color);
          gap: 4px;
        }

        .chart-header .header-group {
          display: flex;
          align-items: center;
          gap: 4px;
        }

        .chart-header .header-separator {
          width: 1px;
          height: 20px;
          background: var(--border-color);
          margin: 0 4px;
        }

        .chart-header .chart-symbol {
          font-weight: 700;
          font-size: 14px;
          color: var(--text-primary);
          margin: 0 4px;
        }

        .chart-header .provider-badge-small {
          display: flex;
          align-items: center;
          gap: 2px;
          padding: 2px;
          border-radius: 4px;
          cursor: pointer;
        }

        .chart-header .provider-badge-small:hover {
          background: var(--bg-tertiary);
        }

        .chart-header .diamond-icon {
          width: 12px;
          height: 12px;
          border: 1px solid var(--text-muted);
          transform: rotate(45deg);
        }

        .chart-header .icon-btn-circle {
          width: 24px;
          height: 24px;
          border-radius: 50%;
          border: 1px solid var(--border-color);
          background: transparent;
          color: var(--text-muted);
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all 0.1s;
        }

        .chart-header .icon-btn-circle:hover {
          color: var(--text-primary);
          border-color: var(--text-muted);
          background: var(--bg-tertiary);
        }

        .chart-header .icon-btn {
          width: 28px;
          height: 28px;
          border: none;
          background: transparent;
          color: var(--text-muted);
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          border-radius: 4px;
        }

        .chart-header .icon-btn:hover {
          color: var(--text-primary);
          background: var(--bg-tertiary);
        }

        .chart-header .indicators-button-group {
          display: flex;
          align-items: center;
          background: transparent;
          border-radius: 4px;
          overflow: hidden;
        }

        .chart-header .indicators-button-group:hover {
          background: var(--bg-tertiary);
        }

        .chart-header .text-icon-btn {
          height: 28px;
          padding: 0 6px;
          border: none;
          background: transparent;
          color: var(--text-muted);
          display: flex;
          align-items: center;
          gap: 4px;
          cursor: pointer;
          font-weight: 600;
          font-size: 13px;
        }

        .chart-header .text-icon-btn:hover {
          color: var(--text-primary);
        }

        .chart-header .dropdown-arrow-btn {
          height: 28px;
          padding: 0 2px;
          border: none;
          background: transparent;
          color: var(--text-muted);
          cursor: pointer;
          display: flex;
          align-items: center;
        }

        .chart-header .dropdown-arrow-btn:hover {
          color: var(--text-primary);
          background: rgba(0, 0, 0, 0.05);
        }

        .active-indicators-menu {
          min-width: 220px;
          padding: 4px 0;
        }

        .active-indicators-menu .menu-header {
          padding: 8px 12px;
          font-size: 11px;
          font-weight: 700;
          color: var(--text-muted);
          text-transform: uppercase;
        }

        .indicator-menu-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 6px 12px;
        }

        .indicator-menu-item:hover {
          background: var(--bg-tertiary);
        }

        .indicator-info {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .color-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }

        .display-name {
          font-size: 13px;
          color: var(--text-primary);
        }

        .indicator-menu-actions {
          display: flex;
          gap: 4px;
        }

        .indicator-menu-actions button {
          background: transparent;
          border: none;
          padding: 4px;
          cursor: pointer;
          color: var(--text-muted);
          border-radius: 4px;
          display: flex;
          align-items: center;
        }

        .indicator-menu-actions button:hover {
          color: var(--text-primary);
          background: rgba(0, 0, 0, 0.05);
        }

        .indicator-menu-actions button.delete:hover {
          color: var(--negative);
        }

        .no-indicators {
          padding: 12px;
          font-size: 12px;
          color: var(--text-muted);
          text-align: center;
        }

        .chart-loading {
          font-size: 11px;
          color: var(--accent-primary);
          margin-left: auto;
          animation: chartPulse 1.5s ease-in-out infinite;
        }

        .indicator-badges {
          display: flex;
          gap: 4px;
          margin-left: 8px;
        }

        .indicator-badge {
          padding: 1px 6px;
          font-size: 9px;
          font-weight: 600;
          border: 1px solid;
          border-radius: 2px;
          background: transparent;
        }

        .indicator-badge.interactable {
          cursor: pointer;
          display: inline-flex;
          align-items: center;
          gap: 4px;
          padding-right: 4px;
        }

        .indicator-badge.interactable:hover {
          background: var(--bg-tertiary);
        }

        .indicator-remove-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          background: transparent;
          border: none;
          color: currentColor;
          opacity: 0.6;
          cursor: pointer;
          padding: 0;
          width: 14px;
          height: 14px;
          border-radius: 50%;
        }

        .indicator-remove-btn:hover {
          opacity: 1;
          background: rgba(0, 0, 0, 0.1);
        }

        @keyframes chartPulse {
          0%,
          100% {
            opacity: 0.5;
          }
          50% {
            opacity: 1;
          }
        }
      `}</style>
    </>
  );
}
