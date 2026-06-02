"""PdfplumberExtractor 단위 테스트.

샘플 PDF는 macOS `cupsfilter`로 생성해 fixtures에 커밋했다. PDF 생성 의존성을
런타임/테스트에 추가하지 않는다(생성은 한 번, 검증은 매번).
"""

from pathlib import Path

import pytest
from app.core.exceptions import PdfParseFailed
from app.services.pdf import PdfplumberExtractor

_FIXTURES = Path(__file__).parent / "fixtures"


def test_extract_korean_and_english_text() -> None:
    pdf_bytes = (_FIXTURES / "sample_resume.pdf").read_bytes()
    result = PdfplumberExtractor().extract(pdf_bytes)
    assert "김지원" in result.text
    assert "FastAPI" in result.text
    assert "jiwon.kim@example.com" in result.text
    assert 0.0 < result.confidence <= 1.0


def test_extract_empty_text_pdf_raises_parse_failed() -> None:
    pdf_bytes = (_FIXTURES / "empty_text.pdf").read_bytes()
    with pytest.raises(PdfParseFailed) as exc_info:
        PdfplumberExtractor().extract(pdf_bytes)
    assert exc_info.value.code == "PDF_PARSE_FAILED"
    assert exc_info.value.details["hint"].startswith("스캔")


def test_extract_corrupt_pdf_raises_parse_failed() -> None:
    with pytest.raises(PdfParseFailed):
        PdfplumberExtractor().extract(b"not a pdf at all")
