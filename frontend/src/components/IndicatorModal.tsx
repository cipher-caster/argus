"use client";

/**
 * Indicator Modal Component
 * Settings modal for adding/editing indicators with configurable parameters
 */

import { IndicatorConfig, useIndicatorStore } from "@/stores/indicatorStore";
import { memo, useEffect, useState } from "react";

interface IndicatorModalProps {
  isOpen: boolean;
  onClose: () => void;
  editingIndicator: IndicatorConfig | null;
}

function IndicatorModalComponent({ isOpen, onClose, editingIndicator }: IndicatorModalProps) {
  const availableIndicators = useIndicatorStore((s) => s.availableIndicators);
  const addIndicator = useIndicatorStore((s) => s.addIndicator);
  const updateIndicator = useIndicatorStore((s) => s.updateIndicator);

  const [selectedType, setSelectedType] = useState<string>("ema");
  const [params, setParams] = useState<Record<string, number>>({});

  const selectedDefinition = availableIndicators.find((i) => i.name === selectedType);

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

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{editingIndicator ? "Edit Indicator" : "Add Indicator"}</h2>
          <button className="close-btn" onClick={onClose}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="modal-body">
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

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button className="btn btn-primary" onClick={handleSubmit}>
            {editingIndicator ? "Update" : "Add"}
          </button>
        </div>

        <style jsx>{`
          .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.7);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            animation: fadeIn 0.15s ease;
          }

          @keyframes fadeIn {
            from {
              opacity: 0;
            }
            to {
              opacity: 1;
            }
          }

          .modal-content {
            width: 100%;
            max-width: 400px;
            background: #12121a;
            border: 1px solid #1a1a2e;
            border-radius: 16px;
            overflow: hidden;
            animation: slideUp 0.2s ease;
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

          .modal-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 20px 24px;
            border-bottom: 1px solid #1a1a2e;
          }

          .modal-header h2 {
            font-size: 18px;
            font-weight: 600;
            color: #ffffff;
            margin: 0;
          }

          .close-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 32px;
            height: 32px;
            background: transparent;
            border: none;
            border-radius: 8px;
            color: #606070;
            cursor: pointer;
            transition: all 0.15s ease;
          }

          .close-btn:hover {
            background: #1a1a2e;
            color: #ffffff;
          }

          .close-btn svg {
            width: 18px;
            height: 18px;
          }

          .modal-body {
            padding: 24px;
          }

          .form-group {
            margin-bottom: 20px;
          }

          .form-group label {
            display: block;
            font-size: 13px;
            font-weight: 500;
            color: #a0a0b0;
            margin-bottom: 8px;
          }

          .param-range {
            color: #606070;
            font-weight: 400;
            margin-left: 8px;
          }

          .form-group select,
          .form-group input {
            width: 100%;
            padding: 12px 16px;
            background: #0a0a0f;
            border: 1px solid #1a1a2e;
            border-radius: 8px;
            color: #ffffff;
            font-size: 15px;
            outline: none;
            transition: border-color 0.15s ease;
          }

          .form-group select:focus,
          .form-group input:focus {
            border-color: #6366f1;
          }

          .form-group select option {
            background: #12121a;
          }

          .description {
            padding: 12px 16px;
            background: rgba(99, 102, 241, 0.1);
            border-radius: 8px;
            color: #a0a0b0;
            font-size: 13px;
            margin: 0;
          }

          .modal-footer {
            display: flex;
            justify-content: flex-end;
            gap: 12px;
            padding: 20px 24px;
            border-top: 1px solid #1a1a2e;
          }

          .btn {
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 500;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
          }

          .btn-secondary {
            background: #1a1a2e;
            color: #a0a0b0;
          }

          .btn-secondary:hover {
            background: #2a2a4a;
            color: #ffffff;
          }

          .btn-primary {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            color: #ffffff;
          }

          .btn-primary:hover {
            opacity: 0.9;
            transform: translateY(-1px);
          }
        `}</style>
      </div>
    </div>
  );
}

export const IndicatorModal = memo(IndicatorModalComponent);
