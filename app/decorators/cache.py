# app/decorators/cache.py
from functools import wraps
from typing import Callable, Optional
import hashlib
import json

def cached(
    ttl: int = 300,
    key_prefix: Optional[str] = None,
    key_builder: Optional[Callable] = None
):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get cache from kwargs or use global
            cache = kwargs.get('cache') or get_global_cache()

            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                prefix = key_prefix or func.__name__
                key_data = json.dumps({"args": args[1:], "kwargs": kwargs}, default=str)
                key_hash = hashlib.md5(key_data.encode()).hexdigest()
                cache_key = f"{prefix}:{key_hash}"

            # Check cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            await cache.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator

# Usage
class BookmarkService:
    def __init__(self, cache: CacheService):
        self.cache = cache

    @cached(ttl=300, key_prefix="product")
    async def get_product(self, product_id: int):
        return await Product.find_by_id(product_id)