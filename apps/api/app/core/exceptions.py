"""Application error hierarchy and FastAPI exception handlers.

Routers MUST NOT raise `HTTPException` directly. Subclass `AppError` and let
the registered handlers translate it to a uniform JSON envelope.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base class for all application-level errors."""

    code: str = "internal_error"
    http_status: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    message_ko: str = "서버 내부 오류가 발생했습니다."

    def __init__(
        self,
        message_ko: str | None = None,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message_ko = message_ko or self.message_ko
        self.details: dict[str, Any] = details or {}
        super().__init__(self.message_ko)


class JobDescriptionNotFound(AppError):
    code = "JD_NOT_FOUND"
    http_status = status.HTTP_404_NOT_FOUND
    message_ko = "채용 공고를 찾을 수 없습니다."


class ResumeNotFound(AppError):
    code = "RESUME_NOT_FOUND"
    http_status = status.HTTP_404_NOT_FOUND
    message_ko = "이력서를 찾을 수 없습니다."


class MatchNotFound(AppError):
    code = "MATCH_NOT_FOUND"
    http_status = status.HTTP_404_NOT_FOUND
    message_ko = "평가 결과를 찾을 수 없습니다."


class PdfParseFailed(AppError):
    code = "PDF_PARSE_FAILED"
    http_status = 422
    message_ko = "PDF에서 텍스트를 추출하지 못했습니다."


class LlmBudgetExceeded(AppError):
    code = "LLM_BUDGET_EXCEEDED"
    http_status = status.HTTP_429_TOO_MANY_REQUESTS
    message_ko = "오늘 사용할 수 있는 AI 분석 한도를 모두 사용했습니다. 내일 다시 시도해 주세요."


class LlmResponseInvalid(AppError):
    code = "LLM_RESPONSE_INVALID"
    http_status = status.HTTP_502_BAD_GATEWAY
    message_ko = "AI 분석 결과를 해석하지 못했습니다. 잠시 후 다시 시도해 주세요."


def _app_error_payload(err: AppError) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "error": {
            "code": err.code,
            "message": err.message_ko,
        }
    }
    if err.details:
        payload["error"]["details"] = err.details
    return payload


def register_exception_handlers(app: FastAPI) -> None:
    """Attach global exception handlers to the FastAPI app."""

    @app.exception_handler(AppError)
    async def _handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        logger.warning("AppError raised", extra={"code": exc.code, "details": exc.details})
        return JSONResponse(
            status_code=exc.http_status,
            content=_app_error_payload(exc),
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception", exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "서버 내부 오류가 발생했습니다.",
                }
            },
        )
