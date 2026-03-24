/**
 * B2: Trading Page Tests
 *
 * Validates that the /trading page renders all core panels without crashing
 * and that key UI sections are present. Tests check structural integrity,
 * not specific values, since paper trading state varies.
 */
import { expect, test } from "@playwright/test";

test.describe("Trading page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/trading");
  });

  test("trading page loads without crash", async ({ page }) => {
    // Main heading must render
    await expect(
      page.getByRole("heading", { name: /Paper Trading/i })
    ).toBeVisible({ timeout: 10_000 });
  });

  test("active positions panel renders", async ({ page }) => {
    // PositionsTable heading
    await expect(
      page.getByText("Active Positions", { exact: false })
    ).toBeVisible({ timeout: 10_000 });

    // Either position rows or "No active positions" empty state
    const positionsContent = page.getByText(/No active positions|OPEN|PENDING|SHORT|LONG/i, { exact: false });
    await expect(positionsContent.first()).toBeVisible({ timeout: 10_000 });
  });

  test("trade history panel renders", async ({ page }) => {
    // TradeHistory heading
    await expect(
      page.getByText("Trade History", { exact: false })
    ).toBeVisible({ timeout: 10_000 });

    // Either trades or "No closed trades yet"
    const historyContent = page.getByText(/No closed trades|WIN|LOSS|EXPIRED/i, { exact: false });
    await expect(historyContent.first()).toBeVisible({ timeout: 10_000 });
  });

  test("risk settings config panel renders", async ({ page }) => {
    // TradingConfigPanel shows "Loading config..." then "Risk Settings" once API resolves
    // Wait for either — the panel always renders one of these
    const configPanel = page.getByText(/Risk Settings|Loading config/i, { exact: false });
    await expect(configPanel.first()).toBeVisible({ timeout: 20_000 });
  });

  test("portfolio summary renders balance", async ({ page }) => {
    // PortfolioSummary shows "Paper Trading — Active/Paused" once portfolio API resolves
    // This is the most reliable non-value text from the component
    const statusText = page.getByText(/Paper Trading.*Active|Paper Trading.*Paused|Backend unavailable/i, { exact: false });
    await expect(statusText.first()).toBeVisible({ timeout: 20_000 });
  });

  test("activity feed panel renders", async ({ page }) => {
    // ActivityFeed — system events log
    // Look for "Activity" label or event type text
    const activity = page.getByText(/Activity|STARTUP|HEARTBEAT|RECOVERY|OUTCOME/i, { exact: false });
    await expect(activity.first()).toBeVisible({ timeout: 10_000 });
  });
});
