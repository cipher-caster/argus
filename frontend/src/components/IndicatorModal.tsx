"use client";

/**
 * Indicator Modal Component
 * Settings modal for adding/editing indicators with configurable parameters
 */

import { IndicatorConfig, useIndicatorStore } from "@/stores/indicatorStore";
import { memo, useEffect, useState } from "react";
import { createPortal } from "react-dom";

interface IndicatorModalProps {
  isOpen: boolean;
  onClose: () => void;
  editingIndicator: IndicatorConfig | null;
}

function IndicatorModalComponent({ isOpen, onClose, editingIndicator }: IndicatorModalProps) {
  const [mounted, setMounted] = useState(false);
  const availableIndicators = useIndicatorStore((s) => s.availableIndicators);
  const addIndicator = useIndicatorStore((s) => s.addIndicator);
  const updateIndicator = useIndicatorStore((s) => s.updateIndicator);

  const [selectedType, setSelectedType] = useState<string>("ema");
  const [params, setParams] = useState<Record<string, number>>({});

  const selectedDefinition = availableIndicators.find((i) => i.name === selectedType);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Initialize form when editing or opening
  useEffect(() => {
    if (isOpen) {
      if (editingIndicator) {
        setSelectedType(editingIndicator.type);
        setParams(editingIndicator.params);
      } else {
        setSelectedType("ema");
        // Set defaults from first indicator
        const def = availableIndicators.find((i) => i.name === "ema");
        if (def) {
          const defaultParams: Record<string, number> = {};
          def.params.forEach((p) => {
            defaultParams[p.name] = p.default;
          });
          setParams(defaultParams);
        }
      }
    }
  }, [isOpen, editingIndicator, availableIndicators]);

  // Update params when indicator type changes
  useEffect(() => {
    if (!editingIndicator && selectedDefinition) {
      const defaultParams: Record<string, number> = {};
      selectedDefinition.params.forEach((p) => {
        defaultParams[p.name] = p.default;
      });
      setParams(defaultParams);
    }
  }, [selectedType, selectedDefinition, editingIndicator]);

  const handleSubmit = () => {
    if (editingIndicator) {
      // Update existing
      const def = availableIndicators.find((i) => i.name === editingIndicator.type);
      updateIndicator(editingIndicator.id, {
        params,
        displayName: `${def?.display_name || editingIndicator.type}(${Object.values(params).join(",")})`,
      });
    } else {
      // Add new
      addIndicator(selectedType, params);
    }
    onClose();
  };

  if (!mounted || !isOpen) return null;

  return (
    <>
      {createPortal(
        <div className="indicator-modal-overlay" onClick={onClose}>
          <div className="indicator-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="indicator-modal-header">
              <h2>{editingIndicator ? "Edit Indicator" : "Add Indicator"}</h2>
              <button className="close-btn" onClick={onClose}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                  <path d="M18 6L6 18M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="indicator-modal-body">
              {/* Indicator Type Selector */}
              {!editingIndicator && (
                <div className="form-group">
                  <label>Indicator Type</label>
                  <select value={selectedType} onChange={(e) => setSelectedType(e.target.value)}>
                    <optgroup label="Overlays">
                      {availableIndicators
                        .filter((i) => i.type === "overlay")
                        .map((i) => (
                          <option key={i.name} value={i.name}>
                            {i.display_name}
                          </option>
                        ))}
                    </optgroup>
                    <optgroup label="Oscillators">
                      {availableIndicators
                        .filter((i) => i.type === "pane")
                        .map((i) => (
                          <option key={i.name} value={i.name}>
                            {i.display_name}
                          </option>
                        ))}
                    </optgroup>
                  </select>
                </div>
              )}

              {/* Parameter Inputs */}
              {selectedDefinition?.params.map((param) => (
                <div key={param.name} className="form-group">
                  <label>
                    {param.name.charAt(0).toUpperCase() + param.name.slice(1)}
                    <span className="param-range">
                      ({param.min} - {param.max})
                    </span>
                  </label>
                  <input
                    type="number"
                    value={params[param.name] ?? param.default}
                    min={param.min}
                    max={param.max}
                    onChange={(e) =>
                      setParams((prev) => ({
                        ...prev,
                        [param.name]: Number(e.target.value),
                      }))
                    }
                  />
                </div>
              ))}

              {/* Description */}
              {selectedDefinition && <p className="description">{selectedDefinition.description}</p>}
            </div>

            <div className="indicator-modal-footer">
              <button className="btn btn-secondary" onClick={onClose}>
                Cancel
              </button>
              <button className="btn btn-primary" onClick={handleSubmit}>
                {editingIndicator ? "Update" : "Add"}
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}

      <style jsx global>{`
        .indicator-modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.7);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 9999;
          animation: indicatorModalFadeIn 0.15s ease;
          backdrop-filter: blur(2px);
        }

        @keyframes indicatorModalFadeIn {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }

        .indicator-modal-content {
          width: 100%;
          max-width: 400px;
          background: #1e1e24;
          border: 1px solid #2d2d3d;
          border-radius: 12px;
          box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 10px 10px -5px rgba(0, 0, 0, 0.2);
          overflow: hidden;
          animation: indicatorModalSlideUp 0.2s ease;
        }

        @keyframes indicatorModalSlideUp {
          from {
            transform: translateY(20px);
            opacity: 0;
          }
          to {
            transform: translateY(0);
            opacity: 1;
          }
        }

        .indicator-modal-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 16px 20px;
          background: #25252e;
          border-bottom: 1px solid #2d2d3d;
        }

        .indicator-modal-header h2 {
          font-size: 16px;
          font-weight: 600;
          color: #ffffff;
          margin: 0;
        }

        .indicator-modal-header .close-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 28px;
          height: 28px;
          background: transparent;
          border: none;
          border-radius: 6px;
          color: #808090;
          cursor: pointer;
          transition: all 0.15s ease;
        }

        .indicator-modal-header .close-btn:hover {
          background: #353545;
          color: #ffffff;
        }

        .indicator-modal-body {
          padding: 20px;
        }

        .indicator-modal-body .form-group {
          margin-bottom: 16px;
        }

        .indicator-modal-body .form-group label {
          display: block;
          font-size: 12px;
          font-weight: 500;
          color: #a0a0b0;
          margin-bottom: 6px;
        }

        .indicator-modal-body .param-range {
          color: #606070;
          font-weight: 400;
          margin-left: 6px;
        }

        .indicator-modal-body .form-group select,
        .indicator-modal-body .form-group input {
          width: 100%;
          padding: 10px 12px;
          background: #14141a;
          border: 1px solid #2d2d3d;
          border-radius: 6px;
          color: #e0e0e0;
          font-size: 14px;
          outline: none;
          transition: border-color 0.15s ease;
        }

        .indicator-modal-body .form-group select:focus,
        .indicator-modal-body .form-group input:focus {
          border-color: #6366f1;
          box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.15);
        }

        .indicator-modal-body .form-group select option {
          background: #14141a;
        }

        .indicator-modal-body .description {
          padding: 10px 12px;
          background: rgba(99, 102, 241, 0.08);
          border-radius: 6px;
          border: 1px solid rgba(99, 102, 241, 0.15);
          color: #c0c0d0;
          font-size: 12px;
          line-height: 1.4;
          margin: 0;
        }

        .indicator-modal-footer {
          display: flex;
          justify-content: flex-end;
          gap: 10px;
          padding: 16px 20px;
          background: #25252e;
          border-top: 1px solid #2d2d3d;
        }

        .indicator-modal-footer .btn {
          padding: 8px 16px;
          font-size: 13px;
          font-weight: 500;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .indicator-modal-footer .btn-secondary {
          background: transparent;
          border: 1px solid #353545;
          color: #a0a0b0;
        }

        .indicator-modal-footer .btn-secondary:hover {
          background: #353545;
          color: #ffffff;
          border-color: #454555;
        }

        .indicator-modal-footer .btn-primary {
          background: #6366f1;
          color: #ffffff;
        }

        .indicator-modal-footer .btn-primary:hover {
          background: #5558dd;
        }
      `}</style>
    </>
  );
}

export const IndicatorModal = memo(IndicatorModalComponent);
