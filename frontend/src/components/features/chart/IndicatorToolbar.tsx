"use client";

/**
 * Indicator Toolbar Component
 * TradingView-style vertical toolbar for managing indicators
 */

import { IndicatorConfig, useIndicatorStore } from "@/stores/indicatorStore";
import { Edit2, Plus, Trash2 } from "lucide-react";
import { memo, useState } from "react";
import { IndicatorModal } from "./IndicatorModal";

import { cn } from "@/lib/utils";

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
      <div className="flex flex-col gap-2 p-3 bg-secondary rounded-xl border border-border shadow-md">
        {/* Add Indicator Button */}
        <button
          className={cn(
            "flex items-center justify-center w-11 h-11 rounded-xl transition-all duration-200 border",
            "bg-gradient-to-br from-primary/10 to-accent-primary/10 text-primary border-primary/20",
            "hover:from-primary/20 hover:to-accent-primary/20 hover:border-primary/40 hover:shadow-[0_4px_12px_rgba(99,102,241,0.2)] hover:-translate-y-0.5"
          )}
          onClick={handleAdd}
          title="Add Indicator"
        >
          <Plus size={20} />
        </button>

        {indicators.length > 0 && <div className="h-px bg-border/50 my-1" />}

        {/* Active Indicators */}
        <div className="flex flex-col gap-2">
          {indicators.map((ind) => (
            <div key={ind.id} className="relative group/item">
              <button
                className={cn(
                  "flex items-center justify-start w-full h-11 px-3 rounded-r-xl rounded-l transition-all duration-200 border-l-[3px]",
                  !ind.visible ? "opacity-50 grayscale" : "opacity-100",
                  "bg-transparent hover:bg-muted text-muted-foreground hover:text-foreground"
                )}
                onClick={() => toggleVisibility(ind.id)}
                title={ind.displayName}
                style={{ borderLeftColor: ind.color }}
              >
                <span className="text-[11px] font-bold tracking-wider uppercase">{ind.type}</span>
              </button>

              {/* Actions Overlay - Desktop Hover */}
              <div className="absolute left-[calc(100%+8px)] top-0 hidden group-hover/item:flex items-center gap-1 p-1 bg-muted border border-border rounded-lg shadow-xl z-50 animate-in fade-in slide-in-from-left-2 duration-150">
                <button className="flex items-center justify-center w-8 h-8 rounded-md text-muted-foreground hover:bg-secondary hover:text-foreground transition-all" onClick={() => handleEdit(ind)} title="Edit">
                  <Edit2 size={16} />
                </button>
                <button className="flex items-center justify-center w-8 h-8 rounded-md text-muted-foreground hover:bg-danger/15 hover:text-danger transition-all" onClick={() => removeIndicator(ind.id)} title="Remove">
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      <IndicatorModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} editingIndicator={editingIndicator} />
    </>
  );
}

export const IndicatorToolbar = memo(IndicatorToolbarComponent);
