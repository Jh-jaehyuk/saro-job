# Changelog

이 프로젝트의 모든 주요 변경 사항은 이 파일에 기록한다.

포맷은 [Keep a Changelog 1.1.0](https://keepachangelog.com/ko/1.1.0/),
버전 규칙은 [Semantic Versioning 2.0.0](https://semver.org/lang/ko/)을 따른다.

태그를 끊는 시점에 `Unreleased` 섹션의 내용을 새 버전 섹션으로 이동시킨다.

## [Unreleased]

### Added
- Git Workflow 규칙 (브랜치 전략, Conventional Commits, 버전 태그) — `AGENTS.md §11`
- `CHANGELOG.md` 초기화
- `.github/pull_request_template.md` — 단일 PR 템플릿 (변경 유형/위험도/체크리스트)
- uv workspace 루트(`pyproject.toml`, `.python-version=3.12`, 공용 dev deps: ruff/mypy/pytest)
- `apps/api` 스캐폴딩: FastAPI 앱(`/health`), `core/{config,db,exceptions,logging}`, `routers/health.py`, `tasks/ping.py`, TDD 테스트 2개, Dockerfile
- `apps/worker` 스캐폴딩: ARQ `WorkerSettings`(ping 등록), 비패키지 워크스페이스 멤버, TDD 테스트 2개, Dockerfile
- Alembic async 환경(`env.py`) + 최초 마이그레이션 `0001_enable_pgvector`
- `docker-compose.yml`: postgres(pgvector)/redis/minio. 리소스 제한 + healthcheck 완화 + profiles(`default`=postgres만, `integration`=전체)
- `.env.example`: DATABASE_URL/REDIS_URL(6380)/S3_* 키
- `.github/workflows/api.yml`, `worker.yml`: paths 필터 CI(ruff·mypy --strict·pytest·alembic)
- `apps/web` 스캐폴딩: Next.js 16(App Router, Turbopack) + React 19 + TypeScript 5 strict + Tailwind 4 + ESLint flat config
- shadcn/ui 초기화: `components.json`, `lib/utils.ts`, `components/ui/button.tsx` (예시 컴포넌트만)
- 루트 페이지(`app/page.tsx`)를 "Hello, saro-job"로 단순화, 메타데이터 한국어화(`app/layout.tsx`)
- Playwright E2E smoke test 1개 (TDD red→green), `playwright.config.ts`
- `apps/web/Dockerfile` (Next.js standalone 출력 활용 슬림 이미지), `apps/web/AGENTS.md` (프론트엔드 전용 규칙)
- `.github/workflows/web.yml`: paths 필터 CI(lint·typecheck·build·playwright e2e)

## [0.0.1] - 2026-05-27

### Added
- 프로젝트 부트스트랩 문서
  - `README.md`
  - `AGENTS.md` — 코드 작성 강제 규칙
  - `docs/PLAN.md` — 초기 의사결정 기록
  - `docs/ARCHITECTURE.md` — 시스템 지도
  - 기능명세서, 와이어프레임
- `.gitignore` (Python·Node·시크릿·OS 커버)
