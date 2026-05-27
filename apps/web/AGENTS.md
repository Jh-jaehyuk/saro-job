# apps/web — Code Authoring Rules

이 파일은 `apps/web` 디렉토리 내부에서만 적용된다. 루트 [`AGENTS.md`](../../AGENTS.md)의
규칙이 우선이며, 여기엔 *프론트엔드 한정 추가 규칙*만 둔다.

<!-- BEGIN:nextjs-agent-rules -->
## Next.js 16

> **이건 당신이 아는 Next.js가 아닐 수 있다.** Next.js 16은 API·관례·파일 구조가
> 학습 데이터와 다를 수 있다. 코드를 쓰기 전에 `node_modules/next/dist/docs/` 안의
> 관련 가이드를 읽고, 사용 중단(deprecation) 알림을 무시하지 말 것.
<!-- END:nextjs-agent-rules -->

## 1. 백엔드와의 경계 (루트 §3 재강조)

- 백엔드 Python 코드를 직접 import 금지. **API 타입은 `apps/web/lib/api-types.ts`
  (openapi-typescript 생성물)만** 사용한다.
- API 호출 클라이언트는 `apps/web/lib/api/`에 두고 TanStack Query로 wrap. 컴포넌트가
  fetch를 직접 호출하지 않는다.

## 2. 컴포넌트

- 모든 컴포넌트는 함수형 + TypeScript. props 인터페이스 명시.
- 서버 컴포넌트가 기본. 상호작용이 필요하면 명시적으로 `"use client"`.
- shadcn/ui 컴포넌트는 `components/ui/` 아래(이 디렉토리는 shadcn cli가 관리).
  도메인 컴포넌트는 `components/<feature>/`.

## 3. 스타일링

- Tailwind 4 사용. 임의의 CSS-in-JS 도입 금지(이유 없이는).
- 디자인 토큰은 `app/globals.css` 또는 Tailwind config에 정의. 컴포넌트에서 임의의
  hex 색상 하드코딩 금지.

## 4. 에러 처리

- API 호출 결과의 `error.code`로 분기, `error.message`를 사용자에게 표시(루트 §6).
- 토스트/배너는 한국어. 코드 식별자는 영문 유지.

## 5. 테스트

- E2E는 Playwright. `e2e/` 디렉토리. 핵심 흐름 1~2개만 유지.
- 컴포넌트 단위 테스트는 *현재 도입하지 않는다*. 도메인 컴포넌트가 복잡해지면 그때
  Vitest/RTL 도입 검토.

## 6. 환경변수

- 클라이언트 노출 변수는 `NEXT_PUBLIC_` 접두사 필수.
- 시크릿(API 키 등)은 절대 `NEXT_PUBLIC_*`로 노출하지 않는다. SSR 또는 API route에서만 사용.
