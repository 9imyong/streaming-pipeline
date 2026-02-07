import { test, expect } from "@playwright/test";

test.describe("Smoke", () => {
  test("1) Streams 목록 로드", async ({ page }) => {
    await page.goto("/streams");
    await expect(page.getByRole("heading", { name: /streams/i })).toBeVisible({ timeout: 10_000 });
    // 테이블 또는 빈 상태/로딩 중 하나
    const table = page.getByRole("table");
    const emptyOrLoading = page.getByText(/no streams|loading|stream/i);
    await expect(table.or(emptyOrLoading)).toBeVisible({ timeout: 10_000 });
  });

  test("2) Stream 상세 진입", async ({ page }) => {
    await page.goto("/streams");
    await expect(page.getByRole("heading", { name: /streams/i })).toBeVisible({ timeout: 10_000 });
    // 첫 번째 stream 상세 링크 클릭 (href=/streams/:id)
    const streamDetailLink = page.locator('a[href^="/streams/"]').first();
    if ((await streamDetailLink.count()) > 0) {
      await streamDetailLink.click();
      await expect(page).toHaveURL(/\/streams\/[^/]+/);
      await expect(page.getByText(/streams|back|detail/i).first()).toBeVisible({ timeout: 5_000 });
    }
  });

  test("3) Settings에 API Key 저장 후 요청 헤더에 포함", async ({ page }) => {
    let sawApiKeyHeader = false;
    page.on("request", (req) => {
      const url = req.url();
      if (url.includes("/v1/") || url.includes("streams") || url.includes("events")) {
        const headers = req.headers();
        if (headers["x-api-key"] === "test-e2e-api-key") sawApiKeyHeader = true;
      }
    });

    await page.goto("/settings");
    await expect(page.getByRole("heading", { name: /settings/i })).toBeVisible({ timeout: 10_000 });

    const apiKeyInput = page.locator('input[type="password"]').first();
    await apiKeyInput.fill("test-e2e-api-key");

    const saveButton = page.getByRole("button", { name: /save/i });
    await saveButton.click();

    await page.goto("/streams");
    await expect(page.getByRole("heading", { name: /streams/i })).toBeVisible({ timeout: 10_000 });

    await page.waitForTimeout(2000);
    expect(sawApiKeyHeader).toBe(true);
  });
});
