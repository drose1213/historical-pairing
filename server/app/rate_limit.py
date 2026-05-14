import logging
from pathlib import Path

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

_slowapi_config_file = Path(__file__).with_name(".slowapi.env")

limiter = Limiter(
    key_func=get_remote_address,
    config_filename=str(_slowapi_config_file),
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    logger.warning("Rate limit exceeded for IP: %s", request.client.host if request.client else "unknown")
    return JSONResponse(
        status_code=429,
        content={
            "detail": "请求过于频繁，请稍后再试",
            "error": "rate_limit_exceeded",
        },
    )


__all__ = ["limiter", "rate_limit_exceeded_handler", "RateLimitExceeded"]
