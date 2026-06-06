"use client";

import { DrawingCanvas } from "@/components/drawing";
import { cn } from "@/lib/utils";
import { Drawing, useDrawingStore } from "@/stores/drawingStore";
import { MouseEventParams } from "lightweight-charts";
import { Trash2, X } from "lucide-react";
import { useEffect, useMemo, useRef } from "react";
import { useChart } from "../context/ChartContext";
import { ChartCoordinateAPI, useChartCoordinates } from "../hooks/useChartCoordinates";

interface DrawingOverlayProps {
  symbol: string;
}

export function DrawingOverlay({ symbol }: DrawingOverlayProps) {
  const coordinateAPI = useChartCoordinates();
  const { chart } = useChart();

  const drawings = useDrawingStore((s) => s.drawings);
  const activeTool = useDrawingStore((s) => s.activeTool);
  const selectedDrawingId = useDrawingStore((s) => s.selectedDrawingId);
  const selectDrawing = useDrawingStore((s) => s.selectDrawing);
  const deleteDrawing = useDrawingStore((s) => s.deleteDrawing);

  // Track when a drawing was last finished so we can ignore the
  // subscribeClick that fires in the same event as the finishing click.
  const lastFinishTimeRef = useRef(0);
  const prevDrawingsLenRef = useRef(drawings.length);
  if (drawings.length > prevDrawingsLenRef.current) {
    lastFinishTimeRef.current = Date.now();
  }
  prevDrawingsLenRef.current = drawings.length;

  // Stable ref so the subscribeClick handler always sees fresh state
  const stateRef = useRef({ drawings, symbol, coordinateAPI, selectDrawing, activeTool });
  useEffect(() => {
    stateRef.current = { drawings, symbol, coordinateAPI, selectDrawing, activeTool };
  });

  // Use chart's own click event for hit-testing — doesn't break pan/zoom
  useEffect(() => {
    if (!chart) return;

    const handler = (params: MouseEventParams) => {
      const { drawings, symbol, coordinateAPI, selectDrawing, activeTool } = stateRef.current;

      if (activeTool) return;
      if (!params.point) return;

      // Ignore the chart click that fires on the same tick as finishing a drawing
      if (Date.now() - lastFinishTimeRef.current < 200) return;

      const { x: px, y: py } = params.point;
      const threshold = 8;
      const symbolDrawings = drawings.filter((d) => d.symbol === symbol);

      for (const drawing of symbolDrawings) {
        if (hitTest(drawing, px, py, threshold, coordinateAPI)) {
          selectDrawing(drawing.id);
          return;
        }
      }

      selectDrawing(null);
    };

    chart.subscribeClick(handler);
    return () => chart.unsubscribeClick(handler);
  }, [chart]);

  const selectedDrawing = useMemo(
    () => drawings.find((d) => d.id === selectedDrawingId) ?? null,
    [drawings, selectedDrawingId]
  );

  const { renderTick, chartWidth, chartHeight } = coordinateAPI;

  // Compute popup position; fall back to top-center if coordinates are off-screen
  const popupPos = useMemo(() => {
    if (!selectedDrawing || !chartWidth || !chartHeight) return null;
    return getPopupPosition(selectedDrawing, coordinateAPI) ?? { x: chartWidth / 2, y: 40 };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDrawing, renderTick, chartWidth, chartHeight]);

  if (!chartWidth || !chartHeight) return null;

  return (
    <>
      <DrawingCanvas coordinateAPI={coordinateAPI} symbol={symbol} />

      {selectedDrawing && popupPos && (
        <div
          className={cn(
            "absolute z-20 flex items-center gap-0.5 px-1 py-1",
            "bg-popover border border-border rounded-lg shadow-lg",
            "pointer-events-auto select-none"
          )}
          style={{
            left: Math.min(Math.max(popupPos.x, 40), chartWidth - 40),
            top: popupPos.y,
            transform: "translateX(-50%)",
          }}
          onMouseDown={(e) => e.stopPropagation()}
          onClick={(e) => e.stopPropagation()}
        >
          <button
            className="flex items-center justify-center w-7 h-7 rounded-md text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
            title="Delete drawing"
            onClick={() => deleteDrawing(selectedDrawing.id)}
          >
            <Trash2 size={14} />
          </button>
          <div className="w-px h-4 bg-border mx-0.5" />
          <button
            className="flex items-center justify-center w-7 h-7 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            title="Deselect"
            onClick={() => selectDrawing(null)}
          >
            <X size={14} />
          </button>
        </div>
      )}
    </>
  );
}

function hitTest(drawing: Drawing, px: number, py: number, threshold: number, api: ChartCoordinateAPI): boolean {
  const { type, points } = drawing;

  if (type === "hline" && points.length >= 1) {
    const coord = api.pointToPixels(points[0]);
    return coord !== null && Math.abs(py - coord.y) < threshold;
  }

  if (type === "vline" && points.length >= 1) {
    const coord = api.pointToPixels(points[0]);
    return coord !== null && Math.abs(px - coord.x) < threshold;
  }

  const pixelPoints = points.map((p) => api.pointToPixels(p)).filter((p): p is { x: number; y: number } => p !== null);
  if (pixelPoints.length === 0) return false;

  if ((type === "trendline" || type === "ray") && pixelPoints.length >= 2) {
    return isNearSegment({ x: px, y: py }, pixelPoints[0], pixelPoints[1], threshold);
  }

  if (type === "rectangle" && pixelPoints.length >= 2) {
    const minX = Math.min(pixelPoints[0].x, pixelPoints[1].x) - threshold;
    const maxX = Math.max(pixelPoints[0].x, pixelPoints[1].x) + threshold;
    const minY = Math.min(pixelPoints[0].y, pixelPoints[1].y) - threshold;
    const maxY = Math.max(pixelPoints[0].y, pixelPoints[1].y) + threshold;
    return px >= minX && px <= maxX && py >= minY && py <= maxY;
  }

  if (type === "fib" && pixelPoints.length >= 2) {
    return (
      Math.abs(py - pixelPoints[0].y) < threshold ||
      Math.abs(py - pixelPoints[1].y) < threshold
    );
  }

  if (type === "text" && pixelPoints.length >= 1) {
    return Math.abs(px - pixelPoints[0].x) < 24 && Math.abs(py - pixelPoints[0].y) < 20;
  }

  return false;
}

function isNearSegment(p: { x: number; y: number }, a: { x: number; y: number }, b: { x: number; y: number }, threshold: number): boolean {
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  const lenSq = dx * dx + dy * dy;
  if (lenSq === 0) return Math.hypot(p.x - a.x, p.y - a.y) < threshold;
  const t = Math.max(0, Math.min(1, ((p.x - a.x) * dx + (p.y - a.y) * dy) / lenSq));
  return Math.hypot(p.x - (a.x + t * dx), p.y - (a.y + t * dy)) < threshold;
}

function getPopupPosition(drawing: Drawing, api: ChartCoordinateAPI): { x: number; y: number } | null {
  const { type, points } = drawing;
  const OFFSET = 38;

  if (type === "hline" && points.length >= 1) {
    const coord = api.pointToPixels(points[0]);
    if (!coord) return null;
    return { x: api.chartWidth / 2, y: Math.max(OFFSET, coord.y - OFFSET) };
  }

  if (type === "vline" && points.length >= 1) {
    const coord = api.pointToPixels(points[0]);
    if (!coord) return null;
    return { x: coord.x, y: OFFSET };
  }

  if (points.length >= 2) {
    const p1 = api.pointToPixels(points[0]);
    const p2 = api.pointToPixels(points[1]);
    if (p1 && p2) {
      return { x: (p1.x + p2.x) / 2, y: Math.max(OFFSET, Math.min(p1.y, p2.y) - 10) };
    }
    if (p1) return { x: p1.x, y: Math.max(OFFSET, p1.y - OFFSET) };
    if (p2) return { x: p2.x, y: Math.max(OFFSET, p2.y - OFFSET) };
  }

  if (points.length >= 1) {
    const p = api.pointToPixels(points[0]);
    if (p) return { x: p.x, y: Math.max(OFFSET, p.y - OFFSET) };
  }

  return null;
}
