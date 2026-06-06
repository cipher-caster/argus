/**
 * B1: Data Rendering Smoke Tests
 *
 * Validates that key data panels render without crashing and show either real
 * data or a graceful empty state. Tests do NOT assert specific values — they
 * guard against shape mismatches that cause blank/broken pages.
 */
import { expect, test } from "@playwright/test";

// ─── Dashboard ───────────────────────────────────────────────────────────────

test.describe("Dashboard data rendering", () => {
  // Run dashboard tests serially — they share the same route and compete for market data
  test.describe.configure({ mode: "serial" });

  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    // Wait for React hydration to complete (CoinTable uses useEffect to mount)
    await page.waitForLoadState("domcontentloaded");
  });

  test("dashboard status bar renders market regime", async ({ page }) => {
    // DashboardStatusBar inline bar shows "BEAR", "BULL", or "UNKNOWN" (not "BEAR Market" — that's modal)
    // "EMA50" label is always present in the scrolling status bar once data loads
    const ema50Text = page.getByText(/EMA50/, { exact: false });
    await expect(ema50Text.first()).toBeVisible({ timeout: 15_000 });
  });

  test("dashboard best setups panel shows cards or empty state", async ({ page }) => {
    // BestSetups component — either setup cards or "No setups" message
    const setupsHeading = page.getByText("Best Setups", { exact: false });
    await expect(setupsHeading.first()).toBeVisible({ timeout: 10_000 });

    // Wait for loading to resolve — either a coin card or empty message appears
    const cardOrEmpty = page.locator(
      '[class*="rounded"][class*="border"], [class*="empty"], [class*="No setups"], [class*="muted"]'
    ).first();
    await expect(cardOrEmpty).toBeVisible({ timeout: 10_000 });
  });

  test("dashboard BTC card renders price", async ({ page }) => {
    // BTCCard always shows BTC price
    // Look for a $ price in the BTC widget area — at minimum a number should render
    const btcPrice = page.getByText(/\$[\d,]+/, { exact: false });
    await expect(btcPrice.first()).toBeVisible({ timeout: 10_000 });
  });

  test("dashboard page structure is complete", async ({ page }) => {
    // Static elements always present regardless of API state
    // Footer link is always rendered
    await expect(page.getByText("View full market table", { exact: false })).toBeVisible({ timeout: 10_000 });
    // Navigation is always present
    await expect(page.locator("nav")).toBeVisible();
  });
});

// ─── Analytics ───────────────────────────────────────────────────────────────

test.describe("Analytics page data rendering", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/analytics");
  });

  test("analytics best setups tab renders on load", async ({ page }) => {
    // Best Setups is the default active tab
    // Either setup rows load or an empty/loading state shows
    const heading = page.getByText("Best Setups", { exact: false });
    await expect(heading.first()).toBeVisible({ timeout: 10_000 });

    // Panel content area appears (not a crash/blank)
    const content = page.locator("main").first();
    await expect(content).toBeVisible();
  });

  test("analytics signal log tab renders after click", async ({ page }) => {
    // Click the Signal Log tab
    const signalLogTab = page.getByRole("button", { name: /Signal Log/i });
    await expect(signalLogTab).toBeVisible({ timeout: 5_000 });
    await signalLogTab.click();

    // Should show signal log content or loading/empty state — not a crash
    const logPanel = page.getByText(/Signal Log/i, { exact: false });
    await expect(logPanel.first()).toBeVisible({ timeout: 10_000 });

    // The main content area should still be visible (no crash/blank)
    await expect(page.locator("main")).toBeVisible();
  });

  test("analytics page sidebar is visible", async ({ page }) => {
    // Sidebar with tab buttons should be present
    const setupsBtn = page.getByRole("button", { name: /Best Setups/i });
    await expect(setupsBtn).toBeVisible({ timeout: 5_000 });

    const signalBtn = page.getByRole("button", { name: /Signal Log/i });
    await expect(signalBtn).toBeVisible({ timeout: 5_000 });
  });
});

// ─── Chart sidebar ───────────────────────────────────────────────────────────

test.describe("Chart page sidebar data rendering", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/chart/BTC-USDT");
    // Wait for chart canvas to confirm page loaded
    await expect(page.locator("canvas").first()).toBeVisible({ timeout: 15_000 });
  });

  test("chart sidebar shows coin details panel", async ({ page }) => {
    // CoinDetailsPanel — shows price, regime, Titan signal
    // At minimum the symbol "BTC" should appear in sidebar
    const sidebar = page.getByText("BTC", { exact: false });
    await expect(sidebar.first()).toBeVisible({ timeout: 10_000 });
  });

  test("chart sidebar signal intel panel loads", async ({ page }) => {
    // CoinSignalIntel panel — shows backtest stats or "no data" state
    // Look for any of: "Win Rate", "Signals", "No signals", "Signal"
    const signalSection = page.getByText(/Win Rate|Signal|Backtest/i, { exact: false });
    await expect(signalSection.first()).toBeVisible({ timeout: 10_000 });
  });
});
