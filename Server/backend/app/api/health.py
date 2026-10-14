from fastapi import APIRouter

router = APIRouter(tags=["system"])


@router.get("/health")
def get_health() -> dict[str, str]:
    """B 백엔드가 요청을 받을 수 있는지 반환한다."""
    return {"status": "ok"}
