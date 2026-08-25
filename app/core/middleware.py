import json
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from redis.asyncio import Redis
from app.core.config import settings
from starlette.concurrency import iterate_in_threadpool

redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)


class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        idempotency_key = request.headers.get("x-idempotency-key")

        if not idempotency_key or request.method in ["GET", "OPTIONS"]:
            return await call_next(request)

        redis_key = f"idempotency:{request.method}:{request.url.path}:{idempotency_key}"

        cached_response = await redis_client.get(redis_key)

        if cached_response:
            data = json.loads(cached_response)
            return Response(
                content=data["body"],
                status_code=data["status_code"],
                media_type="application/json"
            )

        response = await call_next(request)

        if 200 <= response.status_code < 300:
            response_body = [section async for section in response.body_iterator]
            response.body_iterator = iterate_in_threadpool(iter(response_body))

            body_bytes = b"".join(response_body)

            cache_data = json.dumps({
                "status_code": response.status_code,
                "body": body_bytes.decode('utf-8')
            })

            await redis_client.setex(redis_key, 86400, cache_data)

        return response
