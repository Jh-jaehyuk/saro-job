# saro-job

> 채용 담당자를 위한 AI 이력서·JD 매칭과 맞춤형 면접 질문 자동 생성기

**Status**: 🚧 Pre-implementation — 아키텍처·문서만 존재. 코드 스캐폴딩 진행 예정.

## 무엇인가

JD(채용 공고)와 PDF 이력서들을 업로드하면, LLM이 양쪽에서 핵심 키워드를 추출하고
적합도를 **상/중/하**로 분류한다. 부족 역량 기반의 맞춤형 면접 질문 3+개를 자동 생성하고,
합격자 연락처를 CSV로 정리해준다. 멀티테넌트 SaaS, 웹 전용.

타겟 사용자는 기술 직군을 채용하는 중소기업·스타트업의 채용 담당자.

## 문서

| 파일 | 내용 |
|---|---|
| [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) | 시스템 구조 — 모듈 경계·데이터 모델·핵심 흐름·확장 지점 |
| [`docs/PLAN.md`](./docs/PLAN.md) | 초기 스택·설계 의사결정 기록 (왜 이걸 골랐나) |
| [`docs/AI 기반 이력서-JD 매칭 및 면접 질문 생성기_기능명세서_2026-05-26.md`](./docs/) | 기능 명세서 + 수용 기준 |
| [`docs/wireframe/`](./docs/wireframe/) | UI 와이어프레임 |
| [`AGENTS.md`](./AGENTS.md) | AI 코딩 에이전트가 따라야 할 강제 규칙 |

## 스택

| 영역 | 선택 |
|---|---|
| 백엔드 | Python 3.12 · FastAPI · SQLAlchemy 2.0 (async) · Pydantic v2 |
| 비동기 큐 | ARQ (Redis) |
| 프론트엔드 | Next.js (App Router) · TypeScript · shadcn/ui · TanStack Query |
| 데이터베이스 | PostgreSQL + pgvector |
| 오브젝트 스토리지 | Cloudflare R2 (운영) · MinIO (개발) |
| LLM | OpenAI (`LLMClient` 추상화 경유) |
| 인증 | fastapi-users + Authlib (Google OAuth) |
| 배포 | Fly.io |
| 관찰성 | structlog · Sentry · 자체 `LlmCall` 테이블 |

자세한 결정 배경은 [`docs/PLAN.md`](./docs/PLAN.md).

## 개발 환경

스캐폴딩이 끝나면 다음으로 동작 예정:

```bash
docker compose up -d                       # postgres, redis, minio
cd apps/api && uv sync && uvicorn app.main:app --reload
cd apps/worker && arq worker.WorkerSettings
cd apps/web && pnpm install && pnpm dev
```

현재는 placeholder. 스캐폴딩 PR에서 채워진다.

## 라이선스

TBD
