# apps/web

`saro-job`의 웹 프론트엔드. Next.js 16 (App Router) + TypeScript + Tailwind 4 + shadcn/ui.

이 디렉토리 안의 모든 코드는 루트 [`AGENTS.md`](../../AGENTS.md)와
[`./AGENTS.md`](./AGENTS.md) 두 규칙 파일을 동시에 따른다.

## 개발

```bash
pnpm install
pnpm dev               # http://localhost:3000
```

## 검증

```bash
pnpm lint              # ESLint (Next.js flat config)
pnpm typecheck         # tsc --noEmit
pnpm build             # 프로덕션 번들
pnpm test:e2e          # Playwright (smoke 1개)
```

`pnpm test:e2e`는 `playwright.config.ts`가 `pnpm start`로 서버를 띄우므로 사전에
`pnpm build`가 한 번은 실행되어 있어야 한다(CI는 자동).

## 디렉토리

- `app/` — App Router 페이지·레이아웃
- `components/ui/` — shadcn/ui 컴포넌트(cli 관리)
- `components/<feature>/` — 도메인 컴포넌트(향후 PR)
- `lib/` — 유틸·API 클라이언트(`lib/api/`는 향후 PR)
- `e2e/` — Playwright 스펙

## 보일러플레이트와 다음 단계

이 PR(`feat/web-scaffold`)은 Hello 페이지 + 빌드·CI·E2E 토대만 만든다. 인증·도메인
UI는 후속 PR에서 도입된다.
