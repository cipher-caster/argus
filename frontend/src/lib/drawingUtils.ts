/**
 * Drawing Utilities
 * Coordinate conversion between chart coordinates and canvas pixels
 */

import { Point } from "@/stores/drawingStore";

export interface ChartDimensions {
  width: number;
  height: number;
  timeScale: {
    from: number;
    to: number;
  };
  priceScale: {
    from: number;
    to: number;
  };
}

/**
 * Convert a price value to Y pixel coordinate
 */
export function priceToY(price: number, priceFrom: number, priceTo: number, height: number): number {
  const priceRange = priceTo - priceFrom;
  if (priceRange === 0) return height / 2;
  return height - ((price - priceFrom) / priceRange) * height;
}

/**
 * Convert Y pixel coordinate to price value
 */
export function yToPrice(y: number, priceFrom: number, priceTo: number, height: number): number {
  const priceRange = priceTo - priceFrom;
  return priceFrom + ((height - y) / height) * priceRange;
}

/**
 * Convert a time value to X pixel coordinate
 */
export function timeToX(time: number, timeFrom: number, timeTo: number, width: number): number {
  const timeRange = timeTo - timeFrom;
  if (timeRange === 0) return width / 2;
  return ((time - timeFrom) / timeRange) * width;
}

/**
 * Convert X pixel coordinate to time value
 */
export function xToTime(x: number, timeFrom: number, timeTo: number, width: number): number {
  const timeRange = timeTo - timeFrom;
  return timeFrom + (x / width) * timeRange;
}

/**
 * Convert a drawing point to canvas coordinates
 */
export function pointToPixels(point: Point, dimensions: ChartDimensions): { x: number; y: number } {
  return {
    x: timeToX(point.time, dimensions.timeScale.from, dimensions.timeScale.to, dimensions.width),
    y: priceToY(point.price, dimensions.priceScale.from, dimensions.priceScale.to, dimensions.height),
  };
}

/**
 * Convert canvas coordinates to a drawing point
 */
export function pixelsToPoint(x: number, y: number, dimensions: ChartDimensions): Point {
  return {
    time: xToTime(x, dimensions.timeScale.from, dimensions.timeScale.to, dimensions.width),
    price: yToPrice(y, dimensions.priceScale.from, dimensions.priceScale.to, dimensions.height),
  };
}

/**
 * Calculate distance between two points in pixels
 */
export function distanceBetweenPoints(p1: { x: number; y: number }, p2: { x: number; y: number }): number {
  return Math.sqrt(Math.pow(p2.x - p1.x, 2) + Math.pow(p2.y - p1.y, 2));
}

/**
 * Check if a point is near a line segment
 */
export function isPointNearLine(point: { x: number; y: number }, lineStart: { x: number; y: number }, lineEnd: { x: number; y: number }, threshold: number = 5): boolean {
  const d1 = distanceBetweenPoints(point, lineStart);
  const d2 = distanceBetweenPoints(point, lineEnd);
  const lineLen = distanceBetweenPoints(lineStart, lineEnd);

  // Point is near if sum of distances to endpoints is close to line length
  return Math.abs(d1 + d2 - lineLen) < threshold;
}

/**
 * Check if a point is inside a rectangle
 */
export function isPointInRectangle(point: { x: number; y: number }, corner1: { x: number; y: number }, corner2: { x: number; y: number }): boolean {
  const minX = Math.min(corner1.x, corner2.x);
  const maxX = Math.max(corner1.x, corner2.x);
  const minY = Math.min(corner1.y, corner2.y);
  const maxY = Math.max(corner1.y, corner2.y);

  return point.x >= minX && point.x <= maxX && point.y >= minY && point.y <= maxY;
}

/**
 * Get line dash pattern based on style
 */
export function getLineDash(style: "solid" | "dashed" | "dotted"): number[] {
  switch (style) {
    case "dashed":
      return [8, 4];
    case "dotted":
      return [2, 4];
    default:
      return [];
  }
}

/**
 * Calculate Fibonacci price levels
 */
export function calculateFibLevels(startPrice: number, endPrice: number, levels: { level: number; enabled: boolean }[]): { level: number; price: number }[] {
  const priceRange = endPrice - startPrice;

  return levels
    .filter((l) => l.enabled)
    .map((l) => ({
      level: l.level,
      price: startPrice + priceRange * (1 - l.level),
    }));
}
