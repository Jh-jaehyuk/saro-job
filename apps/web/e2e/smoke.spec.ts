import { expect, test } from "@playwright/test";

/**
 * Smoke test — 로그인 페이지가 렌더되고 폼 요소가 모두 보인다.
 *
 * 인증된 흐름(가입 → JD 생성 등) e2e는 백엔드/postgres 의존이라 별도 시나리오 또는
 * 수동 검증으로 다룬다. 이 한 개가 빌드·서버·App Router 마운트·rhf 폼·shadcn UI가
 * 모두 동작함을 증명한다.
 */
test("login page renders form", async ({ page }) => {
  await page.goto("/login");

  await expect(page.getByText("채용 담당자 계정으로 들어오세요.")).toBeVisible();
  await expect(page.getByLabel("이메일")).toBeVisible();
  await expect(page.getByLabel("비밀번호")).toBeVisible();
  await expect(page.getByRole("button", { name: "로그인" })).toBeVisible();
});
