"use client";

/**
 * Indicator Modal Component
 * Settings modal for adding/editing indicators with configurable parameters
 */

import { getNextColor, INDICATOR_COLORS, IndicatorConfig, useIndicatorStore } from "@/stores/indicatorStore";
import { memo, useEffect, useState } from "react";
import { createPortal } from "react-dom";

interface IndicatorModalProps {
  isOpen: boolean;
  onClose: () => void;
  editingIndicator: IndicatorConfig | null;
}

import { cn } from "@/lib/utils";
import { X } from "lucide-react";

function IndicatorModalComponent({ isOpen, onClose, editingIndicator }: IndicatorModalProps) {
  const [mounted, setMounted] = useState(false);
  const availableIndicators = useIndicatorStore((s) => s.availableIndicators);
  const addIndicator = useIndicatorStore((s) => s.addIndicator);
  const updateIndicator = useIndicatorStore((s) => s.updateIndicator);

  const [selectedType, setSelectedType] = useState<string>("ema");
  const [params, setParams] = useState<Record<string, number>>({});
  const [selectedColor, setSelectedColor] = useState<string>(INDICATOR_COLORS[0]);

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
        setSelectedColor(editingIndicator.color);
      } else {
        setSelectedType("ema");
        setSelectedColor(getNextColor());
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
      const def = availableIndicators.find((i) => i.name === editingIndicator.type);
      updateIndicator(editingIndicator.id, {
        params,
        color: selectedColor,
        displayName: `${def?.display_name || editingIndicator.type}(${Object.values(params).join(",")})`,
      });
    } else {
      addIndicator(selectedType, params, selectedColor);
    }
    onClose();
  };

  if (!mounted || !isOpen) return null;

  return (
    <>
      {createPortal(
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm animate-in fade-in duration-200" onClick={onClose}>
          <div className="bg-card border border-border rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 slide-in-from-bottom-4 duration-300" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between px-6 py-4 border-bottom border-border bg-muted/30">
              <h2 className="text-lg font-bold tracking-tight">{editingIndicator ? "Edit Indicator" : "Add Indicator"}</h2>
              <button className="p-1.5 rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-all" onClick={onClose}>
                <X size={20} />
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Indicator Type Selector */}
              {!editingIndicator && (
                <div className="space-y-2">
                  <label className="text-xs font-bold uppercase tracking-widest text-muted-foreground">Indicator Type</label>
                  <select
                    className="w-full bg-secondary border border-border rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-primary/20 outline-none transition-all appearance-none cursor-pointer"
                    value={selectedType}
                    onChange={(e) => setSelectedType(e.target.value)}
                  >
                    <optgroup label="Overlays" className="bg-background">
                      {availableIndicators
                        .filter((i) => i.type === "overlay")
                        .map((i) => (
                          <option key={i.name} value={i.name}>
                            {i.display_name}
                          </option>
                        ))}
                    </optgroup>
                    <optgroup label="Oscillators" className="bg-background">
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
              <div className="space-y-4">
                {selectedDefinition?.params.map((param) => (
                  <div key={param.name} className="space-y-2">
                    <label className="flex justify-between text-xs font-bold uppercase tracking-widest text-muted-foreground">
                      {param.name}
                      <span className="font-medium lowercase text-muted-foreground/60">
                        ({param.min}-{param.max})
                      </span>
                    </label>
                    <input
                      type="number"
                      className="w-full bg-secondary border border-border rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-primary/20 outline-none transition-all"
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
              </div>

              {/* Description */}
              {selectedDefinition && (
                <div className="p-3.5 bg-primary/5 rounded-xl border border-primary/10">
                  <p className="text-[12px] leading-relaxed text-muted-foreground italic font-medium">{selectedDefinition.description}</p>
                </div>
              )}

              {/* Color Picker */}
              <div className="space-y-3">
                <label className="text-xs font-bold uppercase tracking-widest text-muted-foreground">Visual Style</label>
                <div className="flex flex-wrap gap-2.5">
                  {INDICATOR_COLORS.map((c) => (
                    <button
                      key={c}
                      className={cn("w-7 h-7 rounded-full border-2 transition-all hover:scale-110 active:scale-95", selectedColor === c ? "border-foreground scale-110 shadow-lg" : "border-transparent")}
                      style={{ backgroundColor: c }}
                      onClick={() => setSelectedColor(c)}
                    />
                  ))}
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 px-6 py-4 bg-muted/30 border-t border-border">
              <button className="px-5 py-2 text-sm font-bold text-muted-foreground hover:text-foreground hover:bg-muted rounded-xl transition-all" onClick={onClose}>
                Cancel
              </button>
              <button className="px-6 py-2 text-sm font-bold bg-primary text-primary-foreground hover:bg-primary/90 rounded-xl shadow-lg shadow-primary/20 transition-all active:scale-95" onClick={handleSubmit}>
                {editingIndicator ? "Save Changes" : "Add Indicator"}
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </>
  );
}

export const IndicatorModal = memo(IndicatorModalComponent);
