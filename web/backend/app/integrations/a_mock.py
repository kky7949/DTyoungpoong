import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.schemas.process import AnalyzeRequest, AnalyzeResponse


class MockAnalysisProvider:
    def __init__(self, fixture_path: Path | None = None) -> None:
        self.fixture_path = fixture_path or Path(__file__).parents[1] / "mock_data" / "analysis.json"

    def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        """A 연동 시험용 모의 결과를 반환하며 입력 결측값은 변경하지 않는다."""
        del request
        fixture: dict[str, Any] = json.loads(self.fixture_path.read_text(encoding="utf-8"))
        fixture.pop("_meta", None)
        return AnalyzeResponse(
            **fixture,
            generated_at=datetime.now().astimezone(),
            request_id=str(uuid4()),
        )
