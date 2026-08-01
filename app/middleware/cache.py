import time
import json
from datetime import datetime, timedelta
from typing import Callable
from contextvars import ContextVar

from fastapi import FastAPI, HTTPException, Response#, Request
from starlette.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from pydantic import TypeAdapter

from app.config import config
from app.backend.cache.cache import cache_key_builder, get_json, set_json

request_object: ContextVar[Request] = ContextVar('request')

# Redis cache middleware
class RedisCacheMiddleware(BaseHTTPMiddleware):

    use_cache: bool | None = config.cache.use_cache
    skip_cache: bool | None = config.cache.skip_cache
    overwrite_cache: bool | None = config.cache.overwrite_cache

    def __init__(
        self, 
        app: FastAPI
    ): super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:

        request_object.set(request)
        response = await call_next(request)

        # Only cache GET requests
        if request.method != "GET":
            return response
        
        params = request_object.get().query_params
        if params.get('cache') is not None:
            self.cache = TypeAdapter(bool).validate_python(params.get('cache'))
        if params.get('skip_cache') is not None:
            self.skip_cache = TypeAdapter(bool).validate_python(params.get('skip_cache'))

        # Create a cache key
        key = cache_key_builder(self, url=request.url)
    
        # Check cache
        cached_response = get_json(key)
        #cached_response = None
        if cached_response and self.skip_cache is False and self.overwrite_cache is False:
            return JSONResponse(
                content=cached_response["data"],
                status_code=cached_response["status_code"],
                headers={"X-Cache": "HIT", "X-Cache-Generated": cached_response["generated"]}
            )
        
        start_time = time.time()
        # Process request
        process_time = time.time() - start_time
        
        # Cache successful responses
        if 200 <= response.status_code < 300:
            content = b''
            async for chunk in response.body_iterator:
                content += chunk

            response_body = json.loads(content.decode())
            
            cache_data = {
                "data": response_body,
                "generated": json.dumps(datetime.now(), default=str),
                "status_code": response.status_code
            }

            headers={
                "X-Process-Time": str(round(process_time, 4)),
                "X-Cache-Status": "MISS"
            }

            if self.use_cache is True or self.overwrite_cache is True:
                save_to_cache = set_json(key, cache_data)
                headers["X-Cache"] = "SAVED"
                headers["X-Cache-Generated"] = cache_data["generated"]

                if save_to_cache["data"]:
                    response_body = save_to_cache["data"]

            return JSONResponse(
                content=response_body,
                status_code=response.status_code,
                headers=headers
            )
        
        return response
