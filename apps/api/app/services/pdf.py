"""PDFExtractor Port + pdfplumber 어댑터.

라우터/서비스는 pdfplumber를 직접 호출하지 않고 이 인터페이스를 통한다(AGENTS §5).
스캔 PDF의 Tesseract OCR 폴백은 별도 PR에서 추가한다 — 본 구현은 텍스트 PDF만
처리하고, 텍스트가 비어 있으면 명확히 `PdfParseFailed`로 실패시킨다.
"""

import io
from typing import Protocol, runtime_checkable

import pdfplumber

from app.core.exceptions import PdfParseFailed
from app.schemas.resume import PdfExtractResult

# confidence 휴리스틱: 페이지당 평균 문자 수가 이 임계 이상이면 1.0.
# 그 미만은 비례하여 줄이고, 아래 _MIN_CHARS_PER_PAGE 미만은 실패.
_FULL_CONFIDENCE_CHARS_PER_PAGE = 400
_MIN_CHARS_PER_PAGE = 30


@runtime_checkable
class PDFExtractor(Protocol):
    def extract(self, pdf_bytes: bytes) -> PdfExtractResult: ...


class PdfplumberExtractor:
    """pdfplumber 기반 텍스트 추출(OCR 폴백 없음).

    스캔/이미지 PDF는 텍스트 추출량이 적어 `PdfParseFailed`를 던진다 — 후속 PR에서
    Tesseract OCR 폴백이 같은 인터페이스로 들어올 자리.
    """

    def extract(self, pdf_bytes: bytes) -> PdfExtractResult:
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as doc:
                page_count = len(doc.pages)
                text = "\n".join((page.extract_text() or "") for page in doc.pages).strip()
        except Exception as exc:
            raise PdfParseFailed(
                "PDF 파일을 열 수 없습니다.", details={"reason": str(exc)}
            ) from exc

        if page_count == 0 or len(text) < _MIN_CHARS_PER_PAGE * max(1, page_count):
            raise PdfParseFailed(
                details={
                    "pages": page_count,
                    "chars": len(text),
                    "hint": "스캔 이력서일 가능성 — OCR 폴백은 후속 PR에서 지원",
                }
            )

        chars_per_page = len(text) / page_count
        confidence = min(1.0, chars_per_page / _FULL_CONFIDENCE_CHARS_PER_PAGE)
        return PdfExtractResult(text=text, confidence=confidence)
