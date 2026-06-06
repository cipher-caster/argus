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
    <div className="flex items-center justify-between py-1">
      <label className="text-sm text-muted-foreground">{label}</label>
      <div className="flex items-center gap-2 bg-secondary border border-border p-1 rounded-lg">
        <input type="color" value={colors[keyName] || fallback} onChange={(e) => handleColorChange(keyName, e.target.value)} className="w-6 h-6 p-0 border-none bg-transparent cursor-pointer rounded overflow-hidden" />
        <span className="text-[10px] font-mono text-muted-foreground min-w-[50px] uppercase">{colors[keyName] || "Auto"}</span>
        {colors[keyName] && (
          <button className="p-0.5 rounded-md hover:bg-muted text-muted-foreground transition-colors" onClick={() => handleColorChange(keyName, "")} title="Reset to auto">
            <X size={12} />
          </button>
        )}
      </div>
    </div>
  );

  return (
    <>
      {createPortal(
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm animate-in fade-in duration-200" onClick={onClose}>
          <div className="bg-card border border-border rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden animate-in fade-in zoom-in-95 slide-in-from-bottom-4 duration-300" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-muted/30">
              <h2 className="text-lg font-bold tracking-tight">Chart Settings</h2>
              <button className="p-1.5 rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-all" onClick={onClose}>
                <X size={20} />
              </button>
            </div>

            <div className="p-6 space-y-8">
              <div className="space-y-4">
                <h3 className="text-xs font-bold uppercase tracking-widest text-muted-foreground">Candlesticks</h3>

                <div className="grid grid-cols-2 gap-8">
                  <div className="space-y-3">
                    <h4 className="text-sm font-bold border-b border-border pb-2">Bullish (Up)</h4>
                    <div className="space-y-1">
                      <ColorInput label="Body" keyName="upColor" fallback={currentTheme.positive} />
                      <ColorInput label="Borders" keyName="borderUpColor" fallback={currentTheme.positive} />
                      <ColorInput label="Wick" keyName="wickUpColor" fallback={currentTheme.positive} />
                    </div>
                  </div>

                  <div className="space-y-3">
                    <h4 className="text-sm font-bold border-b border-border pb-2">Bearish (Down)</h4>
                    <div className="space-y-1">
                      <ColorInput label="Body" keyName="downColor" fallback={currentTheme.negative} />
                      <ColorInput label="Borders" keyName="borderDownColor" fallback={currentTheme.negative} />
                      <ColorInput label="Wick" keyName="wickDownColor" fallback={currentTheme.negative} />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between px-6 py-4 bg-muted/30 border-t border-border">
              <button className="flex items-center gap-2 px-4 py-2 text-sm font-bold text-muted-foreground hover:text-foreground hover:bg-muted rounded-xl transition-all" onClick={resetColors}>
                <RotateCcw size={14} />
                Reset Defaults
              </button>
              <button className="px-6 py-2 text-sm font-bold bg-primary text-primary-foreground hover:bg-primary/90 rounded-xl shadow-lg shadow-primary/20 transition-all active:scale-95" onClick={onClose}>
                Done
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </>
  );
}

export const ChartSettingsModal = memo(ChartSettingsModalComponent);
