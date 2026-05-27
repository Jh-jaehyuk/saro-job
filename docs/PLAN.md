# AI 기반 이력서-JD 매칭 및 면접 질문 생성기 — 아키텍처 플랜

## Context

`~/Desktop/AI_JD/docs/AI 기반 이력서-JD 매칭 및 면접 질문 생성기_기능명세서_2026-05-26.md`에 정의된 시스템을
구현하기 위한 **초기 아키텍처 결정**을 정리한다. 사용자는 채용 공고(JD)를 입력하고
PDF 이력서 다수를 업로드하며, 시스템은 (1) PDF 파싱 → (2) LLM 키워드 추출 →
(3) 임베딩 기반 적합도(상/중/하) 분류 → (4) 부족 역량 기반 면접 질문 생성 →
(5) 합격자 연락처 CSV 추출 파이프라인을 돈다. 명세상 핵심 수용 기준은
"키워드 추출 90%", "분류 정확도 80%", "연락처 추출 95%", "파싱 오류 5% 이하".

본 플랜은 18개의 결정 트리(배포 형태부터 AGENTS.md 규칙까지)를 사용자와 합의한
결과이며, 다음 단계(스캐폴딩·도메인 모델·첫 엔드포인트 구현) 진입을 위한 합의점이다.

---

## 결정 요약 (스택)

| 영역 | 선택 | 비고 |
|---|---|---|
| 배포 형태 | 멀티테넌트 SaaS (소규모) | 조직 단위는 백엔드에만, MVP UI는 개인 계정 |
| 백엔드 | Python 3.12 + FastAPI | 타입 어노테이션 의무 (AGENTS.md) |
| 프론트엔드 | Next.js (App Router) + TypeScript + shadcn/ui + TanStack Query | OpenAPI→TS 자동 타입 |
| 데이터베이스 | PostgreSQL + pgvector | 관계형 + 벡터 한 DB |
| 비동기 큐 | ARQ (Redis, async-native) | Celery 대신 채택 — 학습 의도 + LLM I/O 친화 |
| LLM 공급자 | OpenAI 단일 직결 | `LLMClient` 추상화 한 겹 |
| 오브젝트 스토리지 | 운영 Cloudflare R2 / 개발 MinIO | S3 호환, 에그레스 무료 |
| 인증 | fastapi-users + Authlib (Google OAuth) | PII 외부 위탁 회피 |
| 인프라 | Fly.io (web / api / worker / postgres / redis 머신) | Docker 기반 |
| 실시간 진행률 | SSE + Redis pub/sub | 단방향, 하트비트 30s, 쿠키 인증 |
| PDF 파싱 | pdfplumber + Tesseract(한국어팩) 폴백 + 정규식/LLM 하이브리드 | `PDFExtractor` 추상화 |
| ORM | SQLAlchemy 2.0 async + Pydantic v2 + Alembic | DB 모델과 API 스키마 분리 |
| 도메인 모델 | `Match(jd_id, resume_id, ...)` 분리형 | JD·Resume 독립, 재평가 가능 |
| 멀티테넌시 | 조직 스코프 (이력서 재사용 가능) | MVP UI는 JD 흐름만 노출 |
| 관찰성 | structlog + Sentry + 자체 `llm_calls` 테이블 | Langfuse는 다음 판으로 유보 |
| 테스트 | pytest + pytest-recording(VCR) + Playwright(최소 E2E) + 별도 evals 스크립트 | |
| 레포 구조 | 모노레포 `apps/{web,api,worker}` | `paths:` 필터로 CI/배포 분리 |
| 시크릿/Config | `.env.example` 커밋, 실제 비밀은 Fly secrets | |

---

## 모노레포 레이아웃

```
/
├── AGENTS.md                  # 이 프로젝트에서 코드 작성 시 강제 규칙
├── README.md
├── docker-compose.yml         # 로컬: postgres+pgvector, redis, minio
├── .github/workflows/         # paths 필터로 web/api/worker 분리
├── apps/
│   ├── web/                   # Next.js (App Router) + shadcn/ui
│   │   ├── app/
│   │   ├── lib/
│   │   │   └── api-types.ts   # openapi-typescript 생성물
│   │   ├── Dockerfile
│   │   └── fly.toml
│   ├── api/                   # FastAPI
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── routers/       # 엔드포인트
│   │   │   ├── services/      # 도메인 서비스
│   │   │   │   ├── llm.py     # LLMClient 추상화
│   │   │   │   ├── pdf.py     # PDFExtractor 추상화
│   │   │   │   └── matching.py
│   │   │   ├── models/        # SQLAlchemy ORM
│   │   │   ├── schemas/       # Pydantic v2
│   │   │   ├── core/          # config, db, sse, exceptions
│   │   │   └── tasks/         # ARQ 잡 함수 (worker에서 import)
│   │   ├── alembic/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── fly.toml
│   └── worker/                # ARQ 워커 진입점
│       ├── worker.py          # apps/api의 tasks 모듈을 import
│       ├── Dockerfile
│       └── fly.toml
└── evals/                     # LLM 평가셋·스크립트 (CI 제외)
```

---

## 핵심 데이터 모델 (개략)

- `Organization` — 멀티테넌시 루트
- `User(org_id)` — fastapi-users
- `JobDescription(org_id, title, raw_text, extracted_requirements_json, embedding)`
- `Resume(org_id, original_pdf_key, parsed_text, sections_json, contact_json,
  parse_confidence, embedding)`
- `Match(jd_id, resume_id, overall_score, category_scores_json, grade,
  matched_keywords_json, missing_keywords_json, status)` — UNIQUE(jd_id, resume_id)
- `InterviewQuestion(match_id, question, question_type, order, edited_by_user)`
- `ResumeProcessingJob(resume_id, jd_id, state, error_json, started_at, finished_at)`
  — ARQ 외부에서 상태를 SSE/UI에 노출하기 위한 거울 테이블
- `LlmCall(id, purpose, model, prompt_hash, prompt, response, tokens_in, tokens_out,
  latency_ms, cost_usd, created_at)` — 자체 관찰성

`Resume.embedding`, `JobDescription.embedding`은 `pgvector.Vector(1536)` (text-embedding-3-small).

---

## 파이프라인 (이력서 1건 처리)

ARQ 워커가 `process_resume(resume_id, jd_id)` 잡을 실행:

1. R2에서 PDF 다운로드 → `PDFExtractor`로 텍스트 추출
2. 텍스트 길이/한글 비율 임계치 미만이면 Tesseract OCR 폴백
3. 정규식으로 이메일·전화 1차 추출 → `contact_json`
4. LLM 호출 1: 섹션 분류(학력/경력/기술) — 결과 `sections_json`
5. LLM 호출 2: 기술/경험 키워드 추출 (구조화 출력, JSON Schema)
6. LLM 호출 3: 이력서 요약 텍스트 임베딩 → `Resume.embedding`
7. JD의 `extracted_requirements_json`과 카테고리별 가중치 점수 계산
8. 코사인 유사도(임베딩) + 키워드 매칭 가중합 → `overall_score`, `grade`
9. grade가 '상'/'중'이면 LLM 호출 4: 부족 역량 기반 면접 질문 3+개 생성
10. LLM 호출 5: 생성된 질문 검증/필터링
11. 각 단계마다 `LlmCall` 기록 + Redis `job:{id}:progress` publish + DB `ResumeProcessingJob.state` 업데이트

FastAPI SSE 엔드포인트 `/jds/{id}/progress`는 Redis pub/sub을 구독, 30초 하트비트.

---

## AGENTS.md에 박을 강제 규칙

```markdown
# AGENTS.md — Code Authoring Rules

## 1. 타입 어노테이션 (Python)
- 모든 `def`/`async def`는 인자와 반환에 타입 명시. 예외 없음.
- `mypy --strict` 또는 `pyright`가 CI에서 통과해야 함.
- `Any`는 외부 SDK 경계에서만, 즉시 도메인 타입으로 좁힌다.

## 2. Pydantic v2
- 외부 경계(HTTP, ARQ payload, LLM 응답, 파일 메타데이터)는 Pydantic v2 모델.
- 함수 사이에서 `dict[str, Any]`를 그대로 흘리지 않는다.
- ORM 모델(SQLAlchemy)과 API 스키마(Pydantic)는 분리. `from_attributes=True`로 매핑.

## 3. 모노레포 경계
- `apps/web`은 백엔드 코드 직접 import 금지. 타입은 `apps/web/lib/api-types.ts`만.
- `apps/worker`는 `apps/api/app/tasks/*`만 import.
- 공통 유틸이 늘면 `packages/`를 신설(현재는 만들지 않는다).

## 4. LLM 호출
- OpenAI SDK 직접 호출 금지. `app.services.llm.LLMClient`를 통해서만.
- 모든 호출은 `LlmCall` 테이블에 기록(purpose, model, prompts, tokens, latency, cost).
- 응답은 가능하면 OpenAI Structured Outputs(JSON Schema)로 받는다.

## 5. PDF 파싱
- `pdfplumber`·`pytesseract`를 라우터/서비스에서 직접 호출 금지.
- `app.services.pdf.PDFExtractor` 프로토콜을 통해서만. 구현체 교체 가능해야 함.

## 6. 에러 처리
- 사용자에게 노출되는 에러는 `app.core.exceptions.AppError` 하위 도메인 예외.
- 라우터에서 `raise HTTPException(...)` 직접 사용 금지. 글로벌 핸들러가 매핑.
- 예외 메시지는 한국어, 코드(`AppError.code`)는 안정적인 영문 식별자.

## 7. 테스트
- LLM/외부 HTTP를 부르는 테스트는 `pytest-recording` 카세트 필수. 카세트 없이 실호출 금지.
- 새 LLM 프롬프트를 도입하면 `evals/`에 평가셋 한 줄 이상 추가.
- E2E는 핵심 흐름 1개만(Playwright). 디테일은 단위/통합으로.

## 8. 시크릿
- `.env` 절대 커밋 금지. `.env.example`만 유지.
- 운영 비밀은 `fly secrets set`. 로컬은 `.env`(gitignored).
- API 키·DB URL이 코드에 하드코딩되면 PR 거절.
```

---

## 위험 / 미결 사항

- **한국어 이력서 폼 다양성**: pdfplumber + Tesseract로 어디까지 커버되는지는
  실제 샘플 20개 벤치마크 전에는 모름. `PDFExtractor` 추상화로 Textract 폴백 여지 유지.
- **OpenAI 단일 공급자 의존**: 장애·정책 변경 시 단일 SPOF. `LLMClient` 추상화로
  Anthropic/Gemini 구현체 추가 비용을 낮춰둠.
- **편향성 검출(§2.1.4)**: 명세에는 있으나 구체적 알고리즘 정의 없음. MVP는
  "민감 속성(나이·성별·국적·학교명) 마스킹 후 LLM 호출" 정도로 시작 → 별도 ADR.
- **R2 PII 위탁**: Cloudflare에 암호화된 PDF가 저장됨. 한국 PIPA상 처리 위탁
  계약 필요. 출시 전 법무 검토.
- **fastapi-users 1.0 미발표**: 다른 인증 라이브러리 변경 가능성 모니터링.

---

## 핵심 파일 (스캐폴딩 단계에 만들 것)

신규 작성이므로 모두 새 파일. 우선순위 순:

1. `AGENTS.md` (위 규칙 그대로)
2. `docker-compose.yml` (postgres+pgvector, redis, minio)
3. `apps/api/app/core/config.py` — pydantic-settings
4. `apps/api/app/core/db.py` — async engine/session
5. `apps/api/app/models/*.py` — 위 데이터 모델
6. `apps/api/alembic/` 초기화 + pgvector 확장 마이그레이션
7. `apps/api/app/services/llm.py` — `LLMClient` 프로토콜 + `OpenAIClient` 구현
8. `apps/api/app/services/pdf.py` — `PDFExtractor` 프로토콜 + `PdfplumberExtractor` + `TesseractFallback`
9. `apps/api/app/tasks/process_resume.py` — ARQ 잡
10. `apps/worker/worker.py` — ARQ WorkerSettings
11. `apps/api/app/routers/` — `auth`, `jds`, `resumes`, `matches`, `progress(SSE)`
12. `apps/web/app/` — 로그인, JD 폼, 업로드, 대시보드, 상세

---

## 검증 (End-to-End)

스캐폴딩 후 다음 시나리오가 손으로 돌아가야 한다:

1. `docker compose up` → postgres, redis, minio 기동
2. `cd apps/api && alembic upgrade head && uvicorn app.main:app --reload`
3. `cd apps/worker && arq worker.WorkerSettings`
4. `cd apps/web && pnpm dev`
5. 브라우저: 가입 → JD 1개 입력 → 샘플 PDF 3개 업로드
6. SSE 진행률이 0→100%로 흐르는 것 확인
7. 대시보드에서 상/중/하 분포 카드 표시
8. 상세 화면에서 매칭 키워드·부족 역량·면접 질문 3개 노출
9. 합격자 CSV 다운로드 → 이메일/전화 포함
10. `pytest`(VCR 카세트 재생) 그린, `pnpm typecheck` 그린

---

## 다음 단계

이 플랜이 승인되면, 첫 PR은 **스캐폴딩 + AGENTS.md + docker-compose + Alembic 초기 마이그레이션**까지로
좁히고, 도메인 모델·LLM 추상화는 두 번째 PR로 분리한다.
