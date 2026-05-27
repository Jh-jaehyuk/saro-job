# AGENTS.md — Code Authoring Rules

이 파일은 이 리포지토리에서 AI 코딩 에이전트가 코드를 쓰거나 수정할 때 따라야 할
**강제 규칙**을 담는다. 의사결정 배경과 시스템 구조는 별도 문서에 있다.

## 먼저 읽을 문서 (모두 `docs/` 아래)

| 파일 | 용도 | 언제 |
|---|---|---|
| [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) | 현재 시스템 지도 — 모듈 경계·데이터 모델·핵심 흐름·확장 지점 | 새 모듈/엔드포인트/잡을 만들기 전에 |
| [`docs/PLAN.md`](./docs/PLAN.md) | 초기 의사결정 기록 — *왜* 이 스택을 골랐는가 | 스택/의존성을 바꾸려 할 때 |
| [`docs/AI 기반 이력서-JD 매칭 및 면접 질문 생성기_기능명세서_*.md`](./docs/) | 기능 명세 (수용 기준 포함) | 새 기능 구현 전 |
| `docs/wireframe/`, `docs/유저플로우.png` | UI 와이어프레임 | 프론트엔드 작업 전 |

본 AGENTS.md와 위 문서가 충돌하면 본 파일이 우선. 본 파일에 명시된 규칙은 협상
대상이 아니며, 위반한 PR은 거절된다. 새 규칙이 필요하면 PR로 이 파일을 갱신한다.

---

## 0. Communication

- 사용자에게 한국어로 응답한다.
- 사용자에게 노출되는 에러 메시지(API 응답·UI 토스트)는 한국어, 코드 식별자는 영문.
- 작업 완료 보고에는 *변경 / 파일 / 검증 / 미실행 / 남은 이슈* 5개 항목을 포함한다.

---

## 1. 타입 어노테이션 (Python)

- 모든 `def` / `async def`는 인자와 반환 타입을 명시한다. 예외 없음.
- `mypy --strict` 또는 `pyright`가 CI에서 통과해야 한다.
- `Any`는 외부 SDK 경계에서만 허용. 즉시 도메인 타입으로 좁힌다.
- `Optional[X]` 대신 `X | None` (PEP 604) 사용.
- SQLAlchemy 2.0 `Mapped[T]` 스타일을 모델에 적용.

---

## 2. Pydantic v2

- 외부 경계(HTTP 요청/응답, ARQ payload, LLM 응답, 파일 메타데이터)는 모두
  Pydantic v2 모델을 거친다.
- 함수 사이에서 `dict[str, Any]`를 그대로 흘리지 않는다.
- ORM 모델(SQLAlchemy)과 API 스키마(Pydantic)는 분리. `from_attributes=True`로
  매핑하되 필드를 자동 노출하지 말고 명시적으로 선언한다.
- 검증 실패 시 `AppError` 하위 도메인 예외로 변환한다(§6).

---

## 3. 모노레포 경계

레이아웃은 [`docs/ARCHITECTURE.md §4`](./docs/ARCHITECTURE.md). 경계 규칙:

- `apps/web`은 백엔드 코드를 직접 import 금지. 타입은 `apps/web/lib/api-types.ts`
  (openapi-typescript 생성물)만 사용한다.
- `apps/worker`는 `apps/api/app/tasks/*`와 `apps/api/app/services/*`만 import한다.
  `apps/api/app/routers/*`는 import 금지.
- 의존 방향: `routers → services → models`. 역방향 import 금지.
  `services → routers` 금지, `core → services` 금지.
- 공통 유틸이 늘면 `packages/`를 신설한다. *현재는 만들지 않는다*.

---

## 4. LLM 호출

- OpenAI SDK를 라우터/태스크에서 직접 호출 금지.
  `apps/api/app/services/llm.py`의 `LLMClient` 인터페이스를 통해서만 호출한다.
- 모든 호출은 `LlmCall` 테이블에 기록한다
  (purpose, model, prompt, response, tokens_in, tokens_out, latency_ms, cost_usd).
- 응답은 가능하면 OpenAI Structured Outputs(JSON Schema)로 받고, Pydantic v2로 검증.
- LLM 호출은 *DB 트랜잭션 밖*에서 한다. 결과 저장만 트랜잭션 안에서(§7).
- 새 프롬프트를 도입하면 `evals/`에 평가셋 한 줄 이상 추가한다.

---

## 5. PDF 파싱

- `pdfplumber`, `pytesseract`를 라우터/서비스에서 직접 호출 금지.
  `apps/api/app/services/pdf.py`의 `PDFExtractor` 프로토콜을 통해서만 호출한다.
- 구현체는 신뢰도 메트릭(`PdfExtractResult.confidence` 등)을 반환한다.
- 텍스트 추출량이 임계치 미만이면 OCR 폴백. 어느 단계가 동작했는지 결과 객체에 표시.
- 50MB 초과, 30페이지 초과, 암호화 PDF는 거절한다(`AppError.PDF_REJECTED`).

---

## 6. 에러 처리

```python
class AppError(Exception):
    code: str          # 안정 식별자, 예: "RESUME_NOT_FOUND"
    http_status: int   # 예: 404
    message_ko: str    # 사용자 표시용 한국어
    details: dict      # 로그/Sentry용, 응답에는 선택 노출
```

- 사용자에게 노출되는 에러는 `AppError` 하위 도메인 예외만 사용.
- 라우터에서 `raise HTTPException(...)`을 직접 호출 금지. 글로벌 핸들러가
  `AppError` → `{"error": {"code": ..., "message": ...}}`로 매핑한다.
- 예외 메시지(`message_ko`)는 한국어, `code`는 안정적인 영문 식별자.
- 미처리 예외는 Sentry로 전송 + 500 + 일반 메시지로 응답.

---

## 7. 트랜잭션 경계

- **HTTP 핸들러**: `Depends(get_session)`이 요청당 트랜잭션 1개를 자동 관리.
  핸들러가 정상 return → commit, 예외 → rollback.
- **`services/*`는 `session.commit()`을 호출하지 않는다.** `session.flush()`만 사용.
- **ARQ task**: 단계별로 새 세션을 열고 단계 끝에서 commit한다. LLM/R2/Redis 등
  외부 호출은 트랜잭션 *밖*에서, 결과 저장만 트랜잭션 *안*에서.
- ARQ 잡은 idempotent해야 한다. 시작 시 `ResumeProcessingJob.step_state_json`을
  확인하여 완료된 단계는 skip.
- 외부 부수효과(R2 업로드, Redis publish)는 결정적 키/멱등 메시지로 짠다.

자세한 시퀀스는 [`docs/ARCHITECTURE.md §6.2`](./docs/ARCHITECTURE.md).

---

## 8. 테넌트 격리

- 모든 services 함수는 호출자의 `user` 또는 `org_id`를 인자로 받는다.
- 모든 쿼리는 `WHERE org_id = current_user.org_id` 필터를 강제한다.
- DB Row Level Security(RLS)는 현재 도입하지 않는다 — services 필터로 격리한다.
  날 SQL 실행 경로(예: 관리자 콘솔)를 추가하려면 ARCHITECTURE.md에 먼저 반영한다.

---

## 9. 테스트

- LLM/외부 HTTP를 부르는 테스트는 `pytest-recording`(VCR) 카세트를 사용한다.
  카세트 없이 실호출 금지. CI는 카세트 재생으로만 동작.
- 점수 계산·정규식 추출 같은 *결정론적 로직*은 pure function으로 분리하고 stdlib만으로
  단위 테스트를 작성한다.
- DB가 필요한 통합 테스트는 testcontainers 또는 SQLite 메모리.
- E2E는 Playwright로 *핵심 흐름 1개만*. 디테일은 단위/통합으로 잡는다.
- 버그 수정은 회귀 테스트를 먼저 짠다(red → green).

검증 순서:
1. 변경한 코드의 가장 좁은 테스트.
2. 모듈/패키지 범위 테스트.
3. 큰 변경이면 리포지토리 전체 검증 명령(`make test` 등).

실패하면 첫 의미 있는 에러부터 근본 원인을 고친다. 실패를 숨기지 않는다.

---

## 10. 시크릿 / 설정

- `.env` 절대 커밋 금지. `.env.example`만 유지한다.
- 운영 비밀은 `fly secrets set`. 로컬은 `.env`(gitignored).
- API 키, DB URL, S3 자격증명, OAuth 클라이언트 시크릿이 코드에 하드코딩되면 PR 거절.
- 환경변수는 모두 `apps/api/app/core/config.py`의 `Settings(BaseSettings)`를 거쳐 읽는다.
  코드 내 `os.environ.get(...)` 직접 사용 금지.

---

## 11. Git Workflow

### 브랜치 전략 (GitHub Flow)

- `main`은 항상 배포 가능한 상태. **`main`에 직접 push 금지**(init 커밋 제외).
  모든 변경은 PR을 통해 머지한다.
- 작업 브랜치는 접두사 + kebab-case 설명을 쓴다:
  - `feat/<설명>` — 새 기능
  - `fix/<설명>` — 버그 수정
  - `chore/<설명>` — 도구·설정·잡일
  - `docs/<설명>` — 문서만 변경
  - `refactor/<설명>` — 동작 불변 리팩터
  - `test/<설명>` — 테스트 추가/수정
- 머지 후 브랜치는 삭제한다.
- 머지 방식은 **squash merge** (PR 1개 = 커밋 1개).

### 커밋 메시지 (Conventional Commits)

```
<type>(<scope>): <짧은 제목, 72자 이내, 한국어 또는 영어>

<본문, 선택>

<footer, 선택 (BREAKING CHANGE, Refs 등)>
```

- `<type>`: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `perf`, `build`, `ci`
- `<scope>`(선택): `api`, `web`, `worker`, `infra`, `deps` 등
- 제목은 명령형 현재시제 ("add X", "fix Y").
- 호환성 깨는 변경은 footer에 `BREAKING CHANGE:` 명시.

### 버전 / 릴리즈

- [Semantic Versioning](https://semver.org)을 따른다: `MAJOR.MINOR.PATCH`.
- 첫 end-to-end 동작 전까지는 `v0.x.y` 프리릴리즈.
- 태그는 수동: `git tag -a v0.1.0 -m "..." && git push origin v0.1.0`.
- 태그 시점에 [`CHANGELOG.md`](./CHANGELOG.md)에 한 섹션 추가
  ([Keep a Changelog](https://keepachangelog.com/) 포맷).
- 릴리즈 자동화(Release Please 등)는 현재 도입하지 않는다.

---

## 12. 일반 엔지니어링 원칙

- 작고 초점이 분명한 변경을 선호한다.
- 기존 아키텍처·네이밍·포맷·파일 구조를 보존한다. 무관한 리팩터·대량 포맷·파일 이동·
  의존성 변경을 같은 PR에 섞지 않는다.
- 공개 API·DB 스키마·마이그레이션·배포 동작·생성물은 작업이 명시적으로 요구할 때만 바꾼다.
- YAGNI. 투기적 추상화를 피한다. ARCHITECTURE.md §8의 Port/Adapter 외에 새
  추상화를 도입하려면 PR 설명에 정당화한다.
- 동작 변경과 순수 리팩터를 가능하면 분리한다.

---

## 13. Safety (파괴적 작업)

다음은 사용자 승인 없이 수행 금지:

- `rm -rf`, `git reset --hard`, `git clean -fdx`, force push
- 대량 reformatting, 무관한 lockfile 재생성
- DB drop/truncate, 비가역 마이그레이션
- 운영 배포, 비가역 인프라 변경

비밀(토큰·키·`.env` 내용)을 커밋하지 않는다. 만질 필요 없는 파일을 덮어쓰거나
되돌리지 않는다.

---

## 14. 의존성 / 환경

- 리포지토리의 패키지 매니저(`uv` for Python, `pnpm` for Node)와 lockfile을 존중한다.
- 새 의존성은 작업이 명시적으로 요구할 때만 추가한다.
- 글로벌 도구를 임의로 설치하지 않는다.
- 필요한 서비스/자격증명/환경변수가 없으면 한계를 설명하고 가능한 로컬 검증을 수행한다.

---

## 15. 최종 보고 포맷

코드/문서를 변경했다면 다음을 포함한다:

```text
변경:
- ...

파일:
- ...

검증:
- `command`: pass/fail
- ...

미실행:
- `command`: reason

남은 이슈:
- ...
```
