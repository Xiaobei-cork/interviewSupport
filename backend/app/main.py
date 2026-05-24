import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import connect_db, close_db
from app.core.logging_config import setup_logging
from app.core.response import parse_error_detail, ok
from app.api import auth, users, interviews, resumes, share, friends, messages, profile, files

settings = get_settings()
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_settings.cache_clear()
    cfg = get_settings()
    Path(cfg.upload_dir).mkdir(parents=True, exist_ok=True)
    if cfg.deepseek_enabled:
        logger.info("DeepSeek 已启用 model=%s base=%s", cfg.deepseek_model, cfg.deepseek_base_url)
    else:
        logger.warning("DeepSeek 未配置 DEEPSEEK_API_KEY，AI 分析/对话将不可用")
    if cfg.oss_enabled:
        logger.info("OSS 已启用 bucket=%s endpoint=%s", cfg.oss_bucket, cfg.oss_endpoint)
    else:
        logger.warning("OSS 未配置，文件将保存到本地 uploads/")
    await connect_db()
    try:
        from app.services.message_service import backfill_social_messages

        stats = await backfill_social_messages()
        if stats["created"]:
            logger.info(
                "站内消息回填：新建 %s 条，跳过 %s 条",
                stats["created"],
                stats["skipped"],
            )
    except Exception as exc:
        logger.warning("站内消息回填跳过（请先执行 alembic upgrade head）: %s", exc)
    logger.info("面试助手 API 启动")
    yield
    await close_db()
    logger.info("面试助手 API 关闭")


app = FastAPI(title="面试助手 API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def access_log_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000
    logging.getLogger("app.access").info(
        "%s %s %s %.1fms",
        request.method,
        request.url.path,
        response.status_code,
        elapsed,
    )
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    code, message = parse_error_detail(exc.detail)
    logger.warning("HTTP异常 %s %s -> %s %s", request.method, request.url.path, code, message)
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": code, "message": message, "data": None},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    message = "；".join(f"{e.get('loc', [])}: {e.get('msg')}" for e in errors[:3])
    logger.warning("参数校验失败 %s %s: %s", request.method, request.url.path, message)
    return JSONResponse(
        status_code=422,
        content={"code": 422, "message": message or "参数校验失败", "data": None},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("未处理异常 %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": "服务器内部错误", "data": None},
    )


prefix = "/api/v1"

app.include_router(auth.router, prefix=prefix)
app.include_router(users.router, prefix=prefix)
app.include_router(interviews.router, prefix=prefix)
app.include_router(resumes.router, prefix=prefix)
app.include_router(share.router, prefix=prefix)
app.include_router(friends.router, prefix=prefix)
app.include_router(messages.router, prefix=prefix)
app.include_router(profile.router, prefix=prefix)
app.include_router(files.router, prefix=prefix)

static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
(static_dir / "avatars").mkdir(exist_ok=True)
app.mount("/api/v1/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/health")
def health():
    cfg = get_settings()
    return ok(
        data={
            "status": "ok",
            "deepseek_mock": not cfg.deepseek_enabled,
            "deepseek_model": cfg.deepseek_model if cfg.deepseek_enabled else None,
            "oss_local": not cfg.oss_enabled,
            "oss_bucket": cfg.oss_bucket if cfg.oss_enabled else None,
        },
        message="服务正常",
    )
