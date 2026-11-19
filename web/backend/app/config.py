import os


DEFAULT_FRONTEND_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)


def get_frontend_origins() -> list[str]:
    """환경변수의 쉼표 구분 origin을 CORS 허용 목록으로 변환한다."""
    configured = os.getenv("FRONTEND_ORIGINS")
    if not configured:
        return list(DEFAULT_FRONTEND_ORIGINS)
    return [origin.strip() for origin in configured.split(",") if origin.strip()]
