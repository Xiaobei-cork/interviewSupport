import json
from typing import Any, Optional

import redis

from app.config import get_settings

_settings = get_settings()
_client: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(_settings.redis_url, decode_responses=True)
    return _client


def cache_get(key: str) -> Optional[Any]:
    try:
        data = get_redis().get(key)
        return json.loads(data) if data else None
    except Exception:
        return None


def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    try:
        get_redis().setex(key, ttl, json.dumps(value, ensure_ascii=False, default=str))
    except Exception:
        pass


def cache_delete(key: str) -> None:
    try:
        get_redis().delete(key)
    except Exception:
        pass
