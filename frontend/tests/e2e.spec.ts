import { expect, test } from "@playwright/test";

const BASE_URL = "http://localhost:3000"; // Default Next.js port

test.describe("Argus MVP E2E Tests", () => {
  test.beforeEach(async ({ page }) => {
    // Go to home before each test
    await page.goto(BASE_URL);
  });

  test("Homepage loads correctly", async ({ page }) => {
    await expect(page).toHaveTitle(/Argus/); // Adjust based on metadata

    // Check for key components
    const brand = page.locator(".brand-name");
    await expect(brand).toHaveText("Argus");

    const statsCards = page.locator(".stats-grid");
    await expect(statsCards).toBeVisible();

    const table = page.locator("table");
    await expect(table).toBeVisible();
  });

  test("Navigation: Market Categories via Widgets", async ({ page }) => {
    // Top Gainers Widget
    const gainersMore = page.locator(".widget-more").first();
    await gainersMore.click();

    await expect(page).toHaveURL(/\/markets\/gainers/);
    await expect(page.locator("h1")).toHaveText("Top Gainers");

    // Back navigation
    await page.locator(".back-link").click();
    await expect(page).toHaveURL(BASE_URL);
  });

  test("Navigation: Chart Page", async ({ page }) => {
    // Click the first coin in the table
    // Assuming the first row link is valid.
    // We'll wait for the table to populate (it might be loading)

    // Ideally look for a specific coin like BTC
    // But dynamic data... let's just click the first row in the main table

    // The main table is consistent.
    const firstRow = page.locator("tbody tr").first();
    await expect(firstRow).toBeVisible();

    // Get the symbol text to verify chart page
    const symbol = await firstRow.locator(".coin-symbol").textContent();
    // Clean symbol? usually "BTC/USDT"

    await firstRow.locator(".coin-link").click();

    // Should navigate to chart
    await expect(page).toHaveURL(/\/chart\/.*/);

    // Verify chart
    await expect(page.locator(".symbol-name")).toBeVisible();
    if (symbol) {
      await expect(page.locator(".symbol-name")).toContainText(symbol);
    }
  });

  test("Navigation: Analyze Button", async ({ page }) => {
    // Wait for table to load
    await expect(page.locator("tbody tr").first()).toBeVisible();

    // Locate the "Analyze" button in the first row
    const analyzeBtn = page.locator("tbody tr").first().locator(".btn-analyze");
    await expect(analyzeBtn).toBeVisible();
    await expect(analyzeBtn).toHaveText("Analyze");

    // Click it
    await analyzeBtn.click();

    // Should navigate to chart
    await expect(page).toHaveURL(/\/chart\/.*/);

    // Verify chart
    await expect(page.locator(".symbol-name")).toBeVisible();
  });

  test("Navigation: Search Functionality", async ({ page }) => {
    const searchInput = page.locator(".search-bar input");
    await searchInput.fill("BTC");

    // Wait for debounce/filtering
    await page.waitForTimeout(1000);

    const rows = page.locator("tbody tr");
    // Should verify at least one row exists and likely BTC
    await expect(rows.first()).toBeVisible();

    const symbol = await rows.first().locator(".coin-symbol").textContent();
    expect(symbol).toContain("BTC");
  });
});
