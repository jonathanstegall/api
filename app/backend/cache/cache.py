import json
import redis
from typing import Optional, Type, TypeVar

from app.config import config
from app.models.base import SQLModel

T = TypeVar("T")

redis_client = redis.Redis(host=config.cache.host, port=config.cache.port, decode_responses=True)

def cache_key_record(record_type: str, record_id: str) -> str:
    return f"{record_type}:{record_id}"

def get_json(key: str) -> Optional[dict]:
    raw = redis_client.execute_command("JSON.GET", key, "$")
    if not raw:
        return None
    # JSON.GET with '$' returns a list-like JSON, take first element
    data = json.loads(raw)[0]
    return data

def set_json(key: str, value: dict, ttl_seconds: int = config.cache.ttl) -> None:
    redis_client.execute_command("JSON.SET", key, "$", json.dumps(value))
    if ttl_seconds:
        redis_client.expire(key, ttl_seconds)

def get_model(key: str, model: Type[T]) -> Optional[T]:
    data = get_json(key)
    if data is None:
        return None
    return data

def set_model(key: str, instance: SQLModel, ttl_seconds: int = config.cache.ttl) -> None:
    set_json(key, json.loads(instance.model_dump_json()), ttl_seconds)
