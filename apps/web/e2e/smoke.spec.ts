import { expect, test } from "@playwright/test";

/**
 * Smoke test — 루트 페이지가 렌더되고 식별 가능한 시그니처 텍스트가 보인다.
 * 이 한 개가 빌드·서버·React 마운트가 모두 동작함을 증명한다.
 */
test("home page renders hello signature", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: /hello, saro-job/i })).toBeVisible();
});
