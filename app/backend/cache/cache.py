import json
import hashlib
import redis
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional, Type, TypeVar

from app.config import config
from app.exceptions import CacheConnectionError, CacheWriteError, CacheReadError
from app.schemas.base import BaseSchema

T = TypeVar("T")

redis_client = redis.Redis(host=config.cache.host, port=6379, decode_responses=True)

def cache_key_builder(
    func: Callable[..., Any],
    **kwargs: Dict[str, Any],
) -> str:
    cache_key = hashlib.md5(  # noqa: S324
        f"{func.__module__}:{kwargs}".encode()
    ).hexdigest()
    return cache_key

def get_json(key: str) -> Optional[dict]:
    # JSON.GET with '$' returns a list-like JSON, take first element
    try:
        raw = redis_client.execute_command("JSON.GET", key, "$")
        #generated = redis_client.execute_command("JSON.GET", "{}_generated".format(key), "$")
        if not raw:
            return None
        data = json.loads(raw)[0]
        return data
    except redis.ConnectionError as e:
        raise CacheConnectionError(f"Redis connection error for cache read ('{key}'): {e}") from e
    except Exception as e:
        # JSON parsing error is a read error
        raise CacheReadError(f"Failed to read JSON from cache ('{key}'): {e}", cache_key=key) from e
    

def set_json(key: str, value: dict, ttl_seconds: int = config.cache.ttl) -> None:
    try:
        #generated = datetime.now()
        save_data = redis_client.execute_command("JSON.SET", key, "$", json.dumps(value))
        #save_time = redis_client.execute_command("JSON.SET", "{}_generated".format(key), "$", json.dumps(generated, default=str))
        #result = {
        #    "save_data": save_data,
        #    "data": value,
        #    "save_time": save_time,
        #    "generated": generated
        #}
        if ttl_seconds:
            redis_client.expire(key, ttl_seconds)
        if save_data == "OK":
            return value
    except redis.ConnectionError as e:
        raise CacheWriteError(f"Redis connection error for cache write ('{key}'): {e}", cache_key=key) from e
    except Exception as e:
        raise CacheWriteError(f"Failed to write JSON to cache ('{key}'): {e}", cache_key=key) from e


def get_schema(key: str, schema: Type[T]) -> Optional[T]:
    data = get_json(key)
    if data is None:
        return None
    #return schema.model_validate(data["data"])
    #result = {
    #    "data": schema.model_validate(data["data"]),
    #    "generated": data["generated"]
    #}
    return data

def set_schema(key: str, instance: BaseSchema, ttl_seconds: int = config.cache.ttl) -> None:
    return set_json(key, json.loads(instance.model_dump_json()), ttl_seconds)
