import os
import time
import asyncio
from typing import Dict, Optional

from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route

from src.stt_tts_loop.response_generator.simple_mcp_client import (
    initialize_mcp,
    get_enhanced_response,
    cleanup_mcp,
)


# Simple in-memory rate limiter per IP (token bucket)
class RateLimiter:
    def __init__(self, capacity: int, refill_per_sec: float) -> None:
        self.capacity = capacity
        self.refill_per_sec = refill_per_sec
        self.tokens: Dict[str, float] = {}
        self.last_refill: Dict[str, float] = {}

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        last = self.last_refill.get(key, now)
        available = self.tokens.get(key, float(self.capacity))
        # Refill
        available = min(
            float(self.capacity),
            available + (now - last) * self.refill_per_sec,
        )
        if available < 1.0:
            self.tokens[key] = available
            self.last_refill[key] = now
            return False
        self.tokens[key] = available - 1.0
        self.last_refill[key] = now
        return True


API_KEY = os.getenv("CHAT_API_KEY", "dev-key")


async def startup() -> None:
    await initialize_mcp()


async def shutdown() -> None:
    await cleanup_mcp()


rate_limiter = RateLimiter(capacity=10, refill_per_sec=0.5)


async def chat_handler(request: Request) -> JSONResponse:
    # Auth
    provided_key = request.headers.get("x-api-key") or request.headers.get("authorization")
    if not provided_key or (provided_key != API_KEY and provided_key != f"Bearer {API_KEY}"):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    # Rate limit
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.allow(client_ip):
        return JSONResponse({"error": "Rate limit exceeded"}, status_code=429)

    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    message: Optional[str] = body.get("message") if isinstance(body, dict) else None
    if not message or not isinstance(message, str):
        return JSONResponse({"error": "Field 'message' is required"}, status_code=400)

    try:
        response_text = await get_enhanced_response(message)
        return JSONResponse({"reply": response_text})
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


routes = [
    Route("/chat", chat_handler, methods=["POST"]),
]


app = Starlette(on_startup=[startup], on_shutdown=[shutdown], routes=routes)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# For local dev: `uvicorn src.chat_api.server:app --host 0.0.0.0 --port 8080`

