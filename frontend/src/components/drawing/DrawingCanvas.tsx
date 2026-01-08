"use client";

/**
 * Drawing Canvas Overlay
 * Canvas layer on top of chart for rendering and interacting with drawings
 */

import { calculateFibLevels, ChartDimensions, getLineDash, pixelsToPoint, pointToPixels } from "@/lib/drawingUtils";
import { formatPrice } from "@/lib/formatters";
import { Drawing, Point, useDrawingStore } from "@/stores/drawingStore";
import { memo, useCallback, useEffect, useRef } from "react";

interface DrawingCanvasProps {
  dimensions: ChartDimensions | null;
  symbol: string;
}

function DrawingCanvasComponent({ dimensions, symbol }: DrawingCanvasProps) {
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
  const selectDrawing = useDrawingStore((s) => s.selectDrawing);
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
    if (!canvas || !dimensions) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Filter drawings for current symbol
    const symbolDrawings = drawings.filter((d) => d.symbol === symbol);

    // Render each drawing
    symbolDrawings.forEach((drawing) => {
      renderDrawing(ctx, drawing, dimensions, drawing.id === selectedDrawingId);
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
      renderDrawing(ctx, tempDrawing, dimensions, false, true);
    }
  }, [drawings, dimensions, symbol, isDrawing, currentPoints, activeTool, selectedDrawingId, defaultStyle, defaultFibLevels]);

  // Re-render when state changes
  useEffect(() => {
    render();
  }, [render]);

  // Mouse handlers
  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      if (!dimensions || !activeTool) return;

      const rect = canvasRef.current?.getBoundingClientRect();
      if (!rect) return;

      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const point = pixelsToPoint(x, y, dimensions);

      startDrawing(point);
    },
    [dimensions, activeTool, startDrawing]
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (!dimensions || !isDrawing) return;

      const rect = canvasRef.current?.getBoundingClientRect();
      if (!rect) return;

      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const point = pixelsToPoint(x, y, dimensions);

      updateDrawing(point);
    },
    [dimensions, isDrawing, updateDrawing]
  );

  const handleMouseUp = useCallback(() => {
    if (!isDrawing) return;

    // For single-click tools
    if (activeTool === "hline" || activeTool === "vline") {
      finishDrawing(symbol);
    } else if (currentPoints.length >= 2) {
      finishDrawing(symbol);
    }
  }, [isDrawing, activeTool, currentPoints, symbol, finishDrawing]);

  const handleClick = useCallback(
    (e: React.MouseEvent) => {
      if (activeTool) return; // Don't select while drawing

      // TODO: Implement drawing selection on click
    },
    [activeTool]
  );

  if (!dimensions) return null;

  return (
    <canvas
      ref={canvasRef}
      width={dimensions.width}
      height={dimensions.height}
      className="drawing-canvas"
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onClick={handleClick}
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        pointerEvents: activeTool ? "auto" : "none",
        cursor: activeTool ? "crosshair" : "default",
      }}
    />
  );
}

/**
 * Render a single drawing to the canvas
 */
function renderDrawing(ctx: CanvasRenderingContext2D, drawing: Drawing, dimensions: ChartDimensions, isSelected: boolean, isPreview: boolean = false) {
  const { type, points, style } = drawing;

  if (points.length === 0) return;

  ctx.save();
  ctx.strokeStyle = style.color;
  ctx.lineWidth = style.lineWidth;
  ctx.setLineDash(getLineDash(style.lineStyle));
  ctx.globalAlpha = isPreview ? 0.6 : 1;

  const pixelPoints = points.map((p) => pointToPixels(p, dimensions));

  switch (type) {
    case "trendline":
    case "ray":
      if (pixelPoints.length >= 2) {
        renderTrendline(ctx, pixelPoints[0], pixelPoints[1], type === "ray", dimensions);
      }
      break;

    case "hline":
      if (pixelPoints.length >= 1) {
        renderHorizontalLine(ctx, pixelPoints[0].y, dimensions.width, points[0].price);
      }
      break;

    case "vline":
      if (pixelPoints.length >= 1) {
        renderVerticalLine(ctx, pixelPoints[0].x, dimensions.height);
      }
      break;

    case "rectangle":
      if (pixelPoints.length >= 2) {
        renderRectangle(ctx, pixelPoints[0], pixelPoints[1], style);
      }
      break;

    case "fib":
      if (pixelPoints.length >= 2 && drawing.fibLevels) {
        renderFibRetracement(ctx, points[0], points[1], drawing.fibLevels, dimensions, style);
      }
      break;

    case "brush":
      if (drawing.brushPath && drawing.brushPath.length > 1) {
        renderBrush(
          ctx,
          drawing.brushPath.map((p) => pointToPixels(p, dimensions))
        );
      }
      break;

    case "text":
      if (pixelPoints.length >= 1 && drawing.text) {
        renderText(ctx, pixelPoints[0], drawing.text, style);
      }
      break;
  }

  // Draw selection handles
  if (isSelected && !isPreview) {
    renderSelectionHandles(ctx, pixelPoints);
  }

  ctx.restore();
}

function renderTrendline(ctx: CanvasRenderingContext2D, start: { x: number; y: number }, end: { x: number; y: number }, extendRight: boolean, dimensions: ChartDimensions) {
  ctx.beginPath();
  ctx.moveTo(start.x, start.y);

  if (extendRight) {
    // Extend ray to right edge
    const slope = (end.y - start.y) / (end.x - start.x);
    const extendedY = start.y + slope * (dimensions.width - start.x);
    ctx.lineTo(dimensions.width, extendedY);
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

  // Price label
  ctx.fillStyle = ctx.strokeStyle;
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

  // Fill
  if (style.fillColor) {
    ctx.globalAlpha = style.fillOpacity ?? 0.1;
    ctx.fillStyle = style.fillColor;
    ctx.fillRect(x, y, w, h);
    ctx.globalAlpha = 1;
  }

  // Stroke
  ctx.strokeRect(x, y, w, h);
}

function renderFibRetracement(ctx: CanvasRenderingContext2D, startPoint: Point, endPoint: Point, fibLevels: { level: number; enabled: boolean; color?: string }[], dimensions: ChartDimensions, style: { color: string }) {
  const levels = calculateFibLevels(startPoint.price, endPoint.price, fibLevels);

  levels.forEach(({ level, price }) => {
    const y = pointToPixels({ time: startPoint.time, price }, dimensions).y;

    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(dimensions.width, y);
    ctx.stroke();

    // Level label
    ctx.fillStyle = style.color;
    ctx.font = "11px Inter, sans-serif";
    ctx.fillText(`${(level * 100).toFixed(1)}% ($${price.toFixed(2)})`, 10, y - 5);
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
