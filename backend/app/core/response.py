"""统一 RESTful 响应格式：{ code, message, data }"""
from typing import Any, Optional

from fastapi import HTTPException
from fastapi.responses import JSONResponse


def ok(
    data: Any = None,
    message: str = "success",
    code: int = 200,
    http_status: int = 200,
) -> JSONResponse:
    return JSONResponse(
        status_code=http_status,
        content={"code": code, "message": message, "data": data},
    )


def created(data: Any = None, message: str = "创建成功") -> JSONResponse:
    return ok(data=data, message=message, code=201, http_status=201)


def api_raise(http_status: int, message: str, code: Optional[int] = None) -> None:
    raise HTTPException(
        status_code=http_status,
        detail={
            "code": code if code is not None else http_status,
            "message": message,
            "data": None,
        },
    )


def parse_error_detail(detail: Any) -> tuple[int, str]:
    if isinstance(detail, dict) and "message" in detail:
        return int(detail.get("code", 500)), str(detail["message"])
    return 500, str(detail)
