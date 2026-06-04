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
- 인증/멀티테넌시 토대: `fastapi-users` 14.x + `httpx-oauth`(Google) 의존성 추가
- SQLAlchemy 모델: `Base` + `TimestampMixin`, `Organization`, `User`(`SQLAlchemyBaseUserTableUUID` + `org_id` FK)
- Alembic 마이그레이션 `0002_organizations_users`(손작성, downgrade 검증)
- `app/core/auth.py`: 쿠키+JWT 백엔드, `UserManager.on_after_register`에서 1인 워크스페이스 자동 생성, `current_active_user` 의존성
- `app/routers/auth.py`: `/auth/{register,cookie/login,cookie/logout}`, `/users/me`, `/auth/google/{authorize,callback}`(OAuth 키 설정 시에만 등록)
- `app/schemas/user.py`: `UserRead/UserCreate/UserUpdate` (fastapi-users 베이스 + `org_id` 노출)
- `Settings`에 `auth_secret_key`, `auth_cookie_*`, `google_oauth_*` 추가 + `.env.example` 갱신
- 인증 흐름 통합 테스트 3개(미인증 401, 가입→로그인→/users/me + org_id 채움, Google OAuth 라우터 smoke)
- 도메인 모델 6종: `JobDescription`, `Resume`, `Match`(UNIQUE(jd_id,resume_id)), `InterviewQuestion`, `ResumeProcessingJob`, `LlmCall`
- pgvector 임베딩 컬럼: `JobDescription.embedding`/`Resume.embedding` = `Vector(1536)` + ivfflat(vector_cosine_ops) 인덱스
- Alembic 마이그레이션 `0003_domain_models`(손작성, up/down 검증)
- Pydantic 읽기 스키마: `JobDescriptionRead/Create`, `ResumeRead`, `PdfExtractResult`, `MatchRead`, `InterviewQuestionRead`
- 도메인 예외: `JobDescriptionNotFound`, `ResumeNotFound`, `MatchNotFound`, `PdfParseFailed`
- Port 추상화 3종: `LLMClient`/`PDFExtractor`(Protocol 인터페이스), `ObjectStorage`(Protocol) + `S3CompatStorage` 구현(boto3 presigned PUT/GET, R2/MinIO 공용)
- `boto3` 의존성 + `boto3-stubs[s3]`(dev) 추가
- Port/모델 테스트 6개(모델 메타데이터 3, presigned URL 유닛 2 + 키 규칙, Protocol 계약 2)
- JD 서비스·라우터: `POST /jds`(생성), `GET /jds`(목록), `GET /jds/{id}`(상세) — org 스코프
- 이력서 업로드: `POST /resumes/upload-url`(presigned PUT 발급 + `Resume` row, 결정적 키), `POST /resumes/{id}/finalize`(`ResumeProcessingJob(queued)` 생성, 멱등). **ARQ enqueue는 보류**(파이프라인 PR)
- Match 조회: `GET /jds/{id}/matches`, `GET /matches/{id}`, `GET /matches/{id}/questions` — JD org 조인으로 테넌트 격리
- `current_org_id` 의존성(인증 사용자 org_id), `get_storage` 의존성 제공자
- 라우터 통합 테스트 12개(JD 4, 이력서 5, Match 3) — 교차 테넌트 404·멱등·미인증 401 포함
- conftest: 전 도메인 테이블 truncate 격리 + 가입/로그인 헬퍼 + storage fake override
- 이력서 처리 파이프라인 오케스트레이션(`app/tasks/process_resume.py:run_resume_pipeline`): parsed→analyzed→embedded→scored→questions→done 단계, 단계별 트랜잭션(외부 호출은 tx 밖), `step_state_json` 기반 멱등 재시도, 실패 시 `state="failed"`/`error_json`
- 스코어링(`app/services/scoring.py`, 순수): 코사인 유사도 + 키워드 매칭 가중합(0.6/0.4) → `overall_score`/`grade`(상≥0.75/중≥0.5/하)/matched·missing
- `ProgressPublisher`(`app/core/sse.py`) Protocol + `NoopProgressPublisher` 기본 구현. 실제 Redis 발행은 SSE PR
- LLMClient Port 진화: `embed`/`structured_completion`이 `(값, LlmUsage)` 튜플 반환 → 파이프라인이 `LlmCall` 기록(§6.2)
- ObjectStorage Port + `S3CompatStorage`에 `get_object(key)->bytes` 추가
- LLM I/O 스키마: `LlmUsage`, `ResumeAnalysis`, `GeneratedQuestions`
- 워커: `process_resume`를 `WorkerSettings.functions`에 등록, `on_startup`에서 ports 주입(실 OpenAI/PDF 어댑터는 placeholder — 어댑터 PR 전까지 실행 시 `NotImplementedError`)
- `redis_url`을 `os.environ` 직접 사용 대신 `get_settings()` 경유로 교정(AGENTS §10)
- 파이프라인 통합 테스트 5개(상 등급 전 단계·하 등급 질문 skip·멱등 재실행·실패 처리·진행률 발행) + scoring 순수 단위 6개
- `PdfplumberExtractor`(`app/services/pdf.py`): pdfplumber 기반 텍스트 PDF 추출, 페이지당 평균 문자 수로 `confidence` 산출, 텍스트 부족 시 `PdfParseFailed`. Tesseract OCR 폴백은 후속 PR
- `app/core/queue.py`: lazy ARQ Redis 풀(`get_arq_pool`) + `QUEUE_NAME` 상수
- `finalize_resume` → ARQ `process_resume` 적재(멱등 — 새 잡일 때만 enqueue). 라우터에 `Depends(get_arq_pool)` 추가
- 워커 `on_startup`: `_NotImplementedPDFExtractor` 제거 → `PdfplumberExtractor` 실 주입. LLM은 여전히 placeholder(다음 PR)
- 샘플 PDF fixture(`apps/api/tests/fixtures/{sample_resume,empty_text}.pdf`) — macOS `cupsfilter`로 1회 생성, PDF 생성 deps 회피
- 테스트 신규: PDF 어댑터 3개(한영 추출, 빈 텍스트 PdfParseFailed, 손상 PDF), finalize ARQ enqueue 1개, 워커 on_startup PDF 와이어링 1개
- ARCHITECTURE §4 PDFExtractor 🟢(텍스트 PDF), §6.2 구현 상태 갱신
- SSE 진행률: `RedisProgressPublisher`(`app/core/sse.py`) — 채널 `jd:{jd_id}:progress`에 JSON 발행
- `app/core/redis.py`: lazy `get_redis()` (#8 queue.py 패턴)
- `Settings.sse_heartbeat_seconds`(기본 30s, 테스트 override 가능)
- 라우터 `app/routers/progress.py`: `GET /jds/{id}/progress`(EventSource, 쿠키 인증, SSE 헤더 + heartbeat), `GET /jds/{id}/status`(재연결 동기화용 잡 목록)
- `jd_service.list_processing_jobs`: JD 소유 검증 후 처리 잡 행 반환
- 워커 `on_startup`: `NoopProgressPublisher` → `RedisProgressPublisher` 교체(redis 클라이언트 ctx 주입)
- CI(`.github/workflows/api.yml`): redis service container(`redis:7-alpine`) 추가
- mypy override에 `redis.*` 추가
- 테스트 신규: redis publisher 1, status 3, SSE 라우터 등록 3, 워커 redis publisher 와이어링 1
- ARCHITECTURE §6.3 🟢 갱신(프론트엔드 EventSource 클라이언트는 🟡 — apps/web 후속)

## [0.0.1] - 2026-05-27

### Added
- 프로젝트 부트스트랩 문서
  - `README.md`
  - `AGENTS.md` — 코드 작성 강제 규칙
  - `docs/PLAN.md` — 초기 의사결정 기록
  - `docs/ARCHITECTURE.md` — 시스템 지도
  - 기능명세서, 와이어프레임
- `.gitignore` (Python·Node·시크릿·OS 커버)
