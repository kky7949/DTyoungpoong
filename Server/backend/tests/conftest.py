import pytest


@pytest.fixture
def anyio_backend() -> str:
    """백엔드 비동기 API 테스트는 Windows에서도 asyncio로 실행한다."""
    return "asyncio"
