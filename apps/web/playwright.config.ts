import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright config for `apps/web` E2E smoke tests.
 *
 * 핵심 흐름 1개에 집중한다(`apps/web/AGENTS.md §5`). 본격적인 흐름 테스트는
 * 도메인 PR에서 도입.
 */
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: "http://127.0.0.1:3000",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    // `pnpm build`가 CI에서 별도로 돌므로 여기선 `next start`로 빌드 산출물을
    // 띄운다. 로컬에서 dev 서버를 띄워두고 테스트하려면 이 블록을 주석 처리하고
    // 사전에 `pnpm dev`를 실행.
    command: "pnpm start",
    url: "http://127.0.0.1:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
