"use client";

/**
 * Drawing Canvas Overlay
 * Canvas layer on top of chart for rendering and interacting with drawings
 */

import { ChartCoordinateAPI } from "@/components/features/chart/hooks/useChartCoordinates";
import { calculateFibLevels, getLineDash } from "@/lib/drawingUtils";
import { formatPrice } from "@/lib/formatters";
import { Drawing, Point, useDrawingStore } from "@/stores/drawingStore";
import { memo, useCallback, useEffect, useRef } from "react";

interface DrawingCanvasProps {
  coordinateAPI: ChartCoordinateAPI;
  symbol: string;
}

function DrawingCanvasComponent({ coordinateAPI, symbol }: DrawingCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const drawings = useDrawingStore((s) => s.drawings);
  const activeTool = useDrawingStore((s) => s.activeTool);
  const isDrawing = useDrawingStore((s) => s.isDrawing);
  const currentPoints = useDrawingStore((s) => s.currentPoints);
  const selectedDrawingId = useDrawingStore((s) => s.selectedDrawingId);
  const defaultStyle = useDrawingStore((s) => s.defaultStyle);
  const defaultFibLevels = useDrawingStore((s) => s.defaultFibLevels);

  const startDrawing = useDrawingStore((s) => s.startDrawing);
  const updateDrawing = useDrawingStore((s) => s.updateDrawing);
  const finishDrawing = useDrawingStore((s) => s.finishDrawing);
  const cancelDrawing = useDrawingStore((s) => s.cancelDrawing);
  const deleteSelected = useDrawingStore((s) => s.deleteSelected);
  const loadFromLocalStorage = useDrawingStore((s) => s.loadFromLocalStorage);

  // Load drawings on mount
  useEffect(() => {
    loadFromLocalStorage(symbol);
  }, [symbol, loadFromLocalStorage]);

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        cancelDrawing();
      } else if (e.key === "Delete" || e.key === "Backspace") {
        deleteSelected();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [cancelDrawing, deleteSelected]);

  // Render all drawings
  const render = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !coordinateAPI.chartWidth || !coordinateAPI.chartHeight) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Filter drawings for current symbol
    const symbolDrawings = drawings.filter((d) => d.symbol === symbol);

    symbolDrawings.forEach((drawing) => {
      renderDrawing(ctx, drawing, coordinateAPI, drawing.id === selectedDrawingId);
    });

    // Render current drawing in progress
    if (isDrawing && currentPoints.length > 0 && activeTool) {
      const tempDrawing: Drawing = {
        id: "temp",
        type: activeTool,
        points: currentPoints,
        style: defaultStyle,
        symbol,
        fibLevels: activeTool === "fib" ? defaultFibLevels : undefined,
        brushPath: activeTool === "brush" ? currentPoints : undefined,
      };
      renderDrawing(ctx, tempDrawing, coordinateAPI, false, true);
    }
  }, [drawings, coordinateAPI, symbol, isDrawing, currentPoints, activeTool, selectedDrawingId, defaultStyle, defaultFibLevels]);

  // Re-render when state or chart view changes (coordinateAPI.renderTick triggers on scroll/zoom)
  useEffect(() => {
    render();
  }, [render]);

  const getPointFromEvent = useCallback(
    (e: React.MouseEvent): Point | null => {
      const rect = canvasRef.current?.getBoundingClientRect();
      if (!rect) return null;
      return coordinateAPI.pixelsToPoint(e.clientX - rect.left, e.clientY - rect.top);
    },
    [coordinateAPI]
  );

  // Mouse handlers — click-click model for 2-point tools (TradingView style)
  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      if (!coordinateAPI.chartWidth || !activeTool) return;

      const point = getPointFromEvent(e);
      if (!point) return;

      if (!isDrawing) {
        // First click: place starting point
        startDrawing(point);
      } else if (activeTool === "brush") {
        // Brush continues accumulating in mousemove
      } else {
        // Second click for 2-point tools: snap endpoint to cursor and finish
        updateDrawing(point);
        finishDrawing(symbol);
      }
    },
    [coordinateAPI, activeTool, isDrawing, startDrawing, updateDrawing, finishDrawing, symbol, getPointFromEvent]
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (!coordinateAPI.chartWidth || !isDrawing) return;

      const point = getPointFromEvent(e);
      if (!point) return;

      updateDrawing(point);
    },
    [coordinateAPI, isDrawing, updateDrawing, getPointFromEvent]
  );

  const handleMouseUp = useCallback(() => {
    if (!isDrawing) return;

    if (activeTool === "hline" || activeTool === "vline") {
      // Single-click tools: finish on mouse release
      finishDrawing(symbol);
    } else if (activeTool === "brush") {
      // Brush: drag-to-draw, finish on release
      finishDrawing(symbol);
    }
    // 2-point tools (trendline, ray, rectangle, fib, text): finished in handleMouseDown on second click
  }, [isDrawing, activeTool, symbol, finishDrawing]);


  if (!coordinateAPI.chartWidth || !coordinateAPI.chartHeight) return null;

  return (
    <canvas
      ref={canvasRef}
      width={coordinateAPI.chartWidth}
      height={coordinateAPI.chartHeight}
      className="drawing-canvas"
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        zIndex: 10,
        pointerEvents: activeTool ? "auto" : "none",
        cursor: activeTool ? "crosshair" : "default",
      }}
    />
  );
}

/**
 * Render a single drawing to the canvas
 */
function renderDrawing(ctx: CanvasRenderingContext2D, drawing: Drawing, api: ChartCoordinateAPI, isSelected: boolean, isPreview: boolean = false) {
  const { type, points, style } = drawing;
  if (points.length === 0) return;

  ctx.save();
  ctx.strokeStyle = style.color;
  ctx.lineWidth = style.lineWidth;
  ctx.setLineDash(getLineDash(style.lineStyle));
  ctx.globalAlpha = isPreview ? 0.6 : 1;

  const pixelPoints = points.map((p) => api.pointToPixels(p)).filter((p): p is { x: number; y: number } => p !== null);

  switch (type) {
    case "trendline":
    case "ray":
      if (pixelPoints.length >= 2) {
        renderTrendline(ctx, pixelPoints[0], pixelPoints[1], type === "ray", api.chartWidth);
      }
      break;

    case "hline":
      if (points.length >= 1) {
        // For horizontal lines, we only need the y (price) coordinate — always renderable
        const yCoord = api.pointToPixels(points[0]);
        if (yCoord) {
          renderHorizontalLine(ctx, yCoord.y, api.chartWidth, points[0].price);
        }
      }
      break;

    case "vline":
      if (pixelPoints.length >= 1) {
        renderVerticalLine(ctx, pixelPoints[0].x, api.chartHeight);
      }
      break;

    case "rectangle":
      if (pixelPoints.length >= 2) {
        renderRectangle(ctx, pixelPoints[0], pixelPoints[1], style);
      }
      break;

    case "fib":
      if (points.length >= 2 && drawing.fibLevels) {
        renderFibRetracement(ctx, points[0], points[1], drawing.fibLevels, api, style);
      }
      break;

    case "brush":
      if (drawing.brushPath && drawing.brushPath.length > 1) {
        const brushPixels = drawing.brushPath.map((p) => api.pointToPixels(p)).filter((p): p is { x: number; y: number } => p !== null);
        renderBrush(ctx, brushPixels);
      }
      break;

    case "text":
      if (pixelPoints.length >= 1 && drawing.text) {
        renderText(ctx, pixelPoints[0], drawing.text, style);
      }
      break;
  }

  if (isSelected && !isPreview) {
    renderSelectionHandles(ctx, pixelPoints);
  }

  ctx.restore();
}

function renderTrendline(ctx: CanvasRenderingContext2D, start: { x: number; y: number }, end: { x: number; y: number }, extendRight: boolean, width: number) {
  ctx.beginPath();
  ctx.moveTo(start.x, start.y);

  if (extendRight) {
    const slope = (end.y - start.y) / (end.x - start.x);
    const extendedY = start.y + slope * (width - start.x);
    ctx.lineTo(width, extendedY);
  } else {
    ctx.lineTo(end.x, end.y);
  }

  ctx.stroke();
}

function renderHorizontalLine(ctx: CanvasRenderingContext2D, y: number, width: number, price: number) {
  ctx.beginPath();
  ctx.moveTo(0, y);
  ctx.lineTo(width, y);
  ctx.stroke();

  ctx.fillStyle = ctx.strokeStyle as string;
  ctx.font = "11px Inter, sans-serif";
  ctx.fillText(`$${formatPrice(price)}`, width - 70, y - 5);
}

function renderVerticalLine(ctx: CanvasRenderingContext2D, x: number, height: number) {
  ctx.beginPath();
  ctx.moveTo(x, 0);
  ctx.lineTo(x, height);
  ctx.stroke();
}

function renderRectangle(ctx: CanvasRenderingContext2D, corner1: { x: number; y: number }, corner2: { x: number; y: number }, style: { fillColor?: string; fillOpacity?: number }) {
  const x = Math.min(corner1.x, corner2.x);
  const y = Math.min(corner1.y, corner2.y);
  const w = Math.abs(corner2.x - corner1.x);
  const h = Math.abs(corner2.y - corner1.y);

  if (style.fillColor) {
    ctx.globalAlpha = style.fillOpacity ?? 0.1;
    ctx.fillStyle = style.fillColor;
    ctx.fillRect(x, y, w, h);
    ctx.globalAlpha = 1;
  }

  ctx.strokeRect(x, y, w, h);
}

function renderFibRetracement(
  ctx: CanvasRenderingContext2D,
  startPoint: Point,
  endPoint: Point,
  fibLevels: { level: number; enabled: boolean; color?: string }[],
  api: ChartCoordinateAPI,
  style: { color: string }
) {
  const levels = calculateFibLevels(startPoint.price, endPoint.price, fibLevels);

  levels.forEach(({ level, price }) => {
    const coord = api.pointToPixels({ time: startPoint.time, price });
    if (!coord) return;

    ctx.beginPath();
    ctx.moveTo(0, coord.y);
    ctx.lineTo(api.chartWidth, coord.y);
    ctx.stroke();

    ctx.fillStyle = style.color;
    ctx.font = "11px Inter, sans-serif";
    ctx.fillText(`${(level * 100).toFixed(1)}% ($${price.toFixed(2)})`, 10, coord.y - 5);
  });
}

function renderBrush(ctx: CanvasRenderingContext2D, points: { x: number; y: number }[]) {
  if (points.length < 2) return;

  ctx.beginPath();
  ctx.moveTo(points[0].x, points[0].y);

  for (let i = 1; i < points.length; i++) {
    ctx.lineTo(points[i].x, points[i].y);
  }

  ctx.stroke();
}

function renderText(ctx: CanvasRenderingContext2D, position: { x: number; y: number }, text: string, style: { color: string; fontSize?: number }) {
  ctx.fillStyle = style.color;
  ctx.font = `${style.fontSize || 14}px Inter, sans-serif`;
  ctx.fillText(text, position.x, position.y);
}

function renderSelectionHandles(ctx: CanvasRenderingContext2D, points: { x: number; y: number }[]) {
  const handleSize = 8;
  ctx.fillStyle = "#6366f1";

  points.forEach((p) => {
    ctx.fillRect(p.x - handleSize / 2, p.y - handleSize / 2, handleSize, handleSize);
  });
}

export const DrawingCanvas = memo(DrawingCanvasComponent);
