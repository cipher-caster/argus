import { expect, test } from "@playwright/test";

const BASE_URL = "http://localhost:3000"; // Default Next.js port

test.describe("Argus MVP E2E Tests", () => {
  test.beforeEach(async ({ page }) => {
    // Go to home before each test
    await page.goto(BASE_URL);
  });

  test("Homepage loads correctly", async ({ page }) => {
    await expect(page).toHaveTitle(/Argus/);

    // Check for Brand Name in Navbar (text "Argus")
    // Use .first() to avoid strict mode if multiple "Argus" texts exist (e.g. meta tags)
    // But specific nav selector is better
    await expect(page.locator("nav").getByText("Argus", { exact: true })).toBeVisible();

    // Check for Top Coins Widgets Header ("Top Gainers")
    await expect(page.getByText("Top Gainers")).toBeVisible();
    await expect(page.getByText("Volume Leaders")).toBeVisible();

    // Check for Table
    await expect(page.locator("table")).toBeVisible();
    // Check for at least one row
    await expect(page.locator("tbody tr").first()).toBeVisible();
  });

  test("Navigation: Market Categories via Widgets", async ({ page }) => {
    // Top Gainers Widget has "View More >"
    // Use locator with text and ensure visibility
    const viewMore = page.locator('a:has-text("View More")').first();
    await expect(viewMore).toBeVisible();
    await viewMore.click();

    // Should navigate to /markets/gainers
    await expect(page).toHaveURL(/\/markets\/gainers/);
  });

  test("Navigation: Chart Page via Table", async ({ page }) => {
    // Wait for table to populate
    const firstRow = page.locator("tbody tr").first();
    await expect(firstRow).toBeVisible();

    // Click the symbol link (inside the 3rd column)
    // Be specific: Look for link starting with /chart/
    const coinLink = firstRow.locator('a[href^="/chart/"]').first();
    await expect(coinLink).toBeVisible();

    await coinLink.click();

    // Should navigate to chart
    await expect(page).toHaveURL(/\/chart\/.*/);

    // Verify chart canvas exists
    await expect(page.locator("canvas").first()).toBeVisible();
  });

  test("Navigation: Search Functionality", async ({ page }) => {
    const searchInput = page.getByPlaceholder("Search coin...");
    await searchInput.fill("BTC");
    // Wait for debounce/filtering
    await page.waitForTimeout(500);

    // Press Enter to go to chart
    await searchInput.press("Enter");

    await expect(page).toHaveURL(/\/chart\/BTC-USDT/);
  });

  test("Analytics Page Loads", async ({ page }) => {
    // Navigate to Analytics via Navbar
    await page.locator("a[href='/analytics']").click();
    await expect(page).toHaveURL(/\/analytics/);

    // Check for Sidebar Header "Futures Data"
    await expect(page.getByText("Futures Data")).toBeVisible();

    // Check for "Funding Rate" menu item - using Role Button to resolve ambiguity
    await expect(page.getByRole("button", { name: "Funding Rate", exact: true })).toBeVisible();

    // Check for SVGs (charts)
    await expect(page.locator("svg").first()).toBeVisible();
  });

  test("Chart Page Features: Refresh & Navbar", async ({ page }) => {
    // Navigate via "Charts" link
    await page.locator("a[href='/chart/BTC-USDT']").click();

    await expect(page).toHaveURL(/\/chart\/BTC-USDT/);

    // Check for Refresh Button (using title attribute)
    const refreshBtn = page.locator("button[title='Refresh Chart Data']");
    await expect(refreshBtn).toBeVisible();
    // Verify it is enabled (not disabled)
    await expect(refreshBtn).toBeEnabled();
  });
});
