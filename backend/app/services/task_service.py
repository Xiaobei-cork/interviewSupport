import asyncio
import json
import uuid
from typing import Any, Callable, Awaitable

from app.utils.redis_client import get_redis

STAGES = [
    ("parsing", "正在解析内容...", 20),
    ("extracting", "正在提取关键信息...", 50),
    ("analyzing", "正在生成分析结果...", 75),
    ("generating", "正在生成优化建议...", 90),
    ("done", "分析完成", 100),
]


def create_task() -> str:
    task_id = uuid.uuid4().hex
    data = {"status": "pending", "progress": 0, "stage": "", "message": "", "result": None}
    get_redis().setex(f"task:{task_id}", 3600, json.dumps(data, ensure_ascii=False))
    return task_id


def update_task(task_id: str, **kwargs: Any) -> None:
    r = get_redis()
    key = f"task:{task_id}"
    raw = r.get(key)
    data = json.loads(raw) if raw else {}
    data.update(kwargs)
    r.setex(key, 3600, json.dumps(data, ensure_ascii=False, default=str))


def get_task(task_id: str) -> dict | None:
    raw = get_redis().get(f"task:{task_id}")
    return json.loads(raw) if raw else None


async def run_task(task_id: str, worker: Callable[[], Awaitable[Any]]) -> None:
    try:
        for stage, msg, progress in STAGES[:-1]:
            update_task(task_id, status="running", stage=stage, message=msg, progress=progress)
            await asyncio.sleep(0.8 if not __import__("app.config", fromlist=["get_settings"]).get_settings().deepseek_enabled else 0.3)
        result = await worker()
        update_task(
            task_id,
            status="done",
            stage="done",
            message="分析完成",
            progress=100,
            result=result,
        )
    except Exception as e:
        update_task(task_id, status="error", message=str(e), progress=0)


def mock_transcript() -> str:
    return (
        "面试官：请介绍一下你最近的项目。\n"
        "候选人：我负责了后端API的设计与实现，使用FastAPI和MySQL，"
        "日活约10万，接口响应时间优化到50ms以内。\n"
        "面试官：遇到的最大挑战是什么？\n"
        "候选人：主要是高并发下的数据库瓶颈，通过Redis缓存和读写分离解决。"
    )
