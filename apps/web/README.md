# apps/web

`saro-job`의 웹 프론트엔드. Next.js 16 (App Router) + TypeScript + Tailwind 4 + shadcn/ui +
TanStack Query.

이 디렉토리 안의 모든 코드는 루트 [`AGENTS.md`](../../AGENTS.md)와
[`./AGENTS.md`](./AGENTS.md) 두 규칙 파일을 동시에 따른다.

## 환경변수

`.env.local`(개발) 또는 `.env.example` 참고:

- `NEXT_PUBLIC_API_BASE_URL` — `/api/*` rewrite의 백엔드 목적지(기본 `http://localhost:8000`).
- `NEXT_PUBLIC_GOOGLE_OAUTH_ENABLED` — `"true"`면 로그인 페이지에 Google 버튼 표시.

## 백엔드 API 타입 동기화

`lib/api-types.ts`는 `openapi-typescript` 생성물이다. 백엔드 OpenAPI 스키마가
바뀌면 다음 스크립트로 재생성하고 함께 커밋한다.

```bash
# 사전: 백엔드를 :8000에 띄워둠
pnpm openapi:generate
```

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
pnpm test:e2e          # Playwright (smoke 1개, 백엔드 불필요)
```

`pnpm test:e2e`는 `playwright.config.ts`가 `pnpm start`로 서버를 띄우므로 사전에
`pnpm build`가 한 번은 실행되어 있어야 한다(CI는 자동).

## 디렉토리

- `app/` — App Router 페이지·레이아웃
  - `(auth)/{login,register}` — 인증 페이지
  - `(app)/jds` — 인증 후 진입(JD 목록·상세). 레이아웃이 `useMe` 401 시 `/login`으로 리다이렉트.
- `components/ui/` — shadcn/ui (cli 관리)
- `components/{auth,jds,app,providers}/` — 도메인 컴포넌트
- `lib/api/` — fetch wrapper + 백엔드 호출(`client.ts`/`auth.ts`/`jds.ts`)
- `lib/queries/` — TanStack Query 훅
- `lib/api-types.ts` — openapi-typescript 생성물
- `e2e/` — Playwright 스펙

## 인증 흐름

1. `/register` → 가입 → 자동 로그인 → `/jds`로 이동
2. `/login` → 이메일/비번 로그인 → `/jds`
3. (app) 레이아웃의 `useMe`가 401을 받으면 `/login`으로 리다이렉트
4. 로그아웃 시 `queryClient.clear()`로 캐시 폐기

## 안 하는 것 (후속 PR)

이 PR(`feat/web-auth-and-jds`)은 인증 + JD CRUD까지만. 이력서 업로드, 대시보드, 매칭 상세,
SSE EventSource 구독은 다음 web PR.
