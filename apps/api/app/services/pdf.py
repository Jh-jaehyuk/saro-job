"""PDFExtractor Port.

구현체(pdfplumber + Tesseract OCR 폴백)는 파이프라인 PR에서 추가한다. 여기서는
계약만 확정한다. 라우터/서비스는 pdfplumber·pytesseract를 직접 호출하지 않고
이 인터페이스를 통한다(AGENTS §5).
"""

from typing import Protocol, runtime_checkable

from app.schemas.resume import PdfExtractResult


@runtime_checkable
class PDFExtractor(Protocol):
    def extract(self, pdf_bytes: bytes) -> PdfExtractResult: ...
