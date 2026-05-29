"""Port Protocol 계약 회귀 방지 테스트.

더미 구현이 Protocol을 구조적으로 만족하는지 확인한다. 시그니처가 바뀌어 계약이
깨지면 여기서 잡힌다.
"""

from app.schemas.resume import PdfExtractResult
from app.services.llm import LLMClient
from app.services.pdf import PDFExtractor


class _FakePdfExtractor:
    def extract(self, pdf_bytes: bytes) -> PdfExtractResult:
        return PdfExtractResult(text="hello", confidence=1.0)


class _FakeLLMClient:
    async def embed(self, text: str) -> list[float]:
        return [0.0] * 1536

    async def structured_completion(
        self, *, purpose: str, system: str, user: str, schema: type[PdfExtractResult]
    ) -> PdfExtractResult:
        return PdfExtractResult(text=user, confidence=0.5)


def test_fake_pdf_extractor_satisfies_protocol() -> None:
    extractor: PDFExtractor = _FakePdfExtractor()
    assert isinstance(extractor, PDFExtractor)
    assert extractor.extract(b"%PDF").text == "hello"


def test_fake_llm_client_satisfies_protocol() -> None:
    client: LLMClient = _FakeLLMClient()
    assert isinstance(client, LLMClient)
