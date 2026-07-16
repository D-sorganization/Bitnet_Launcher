"""FastAPI server for BitNet Launcher."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from bitnet_launcher.config import BitnetConfig, InferenceConfig
from bitnet_launcher.models import ModelInfo, discover_models
from bitnet_launcher.runners import LocalLlamaRunner

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan manager for the FastAPI application."""
    logger.info("Starting BitNet API server")
    yield
    logger.info("Shutting down BitNet API server")


app = FastAPI(
    title="BitNet Launcher API",
    description="REST API for discovering and interacting with BitNet models",
    version="0.1.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def add_security_headers(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "img-src 'self' data: https://fastapi.tiangolo.com;"
    )
    return response


config = BitnetConfig()


class ModelResponse(BaseModel):
    """API response model for a discovered BitNet model."""

    name: str
    path: str
    size_bytes: int


class ChatStartRequest(BaseModel):
    """Request model for starting a chat session."""

    model_name: str = Field(max_length=128)


class ChatSendRequest(BaseModel):
    """Request model for sending a message."""

    model_name: str = Field(max_length=128)
    message: str = Field(max_length=4096)


@app.get("/models")
async def list_models() -> list[ModelResponse]:
    """List all locally installed BitNet models."""
    models: list[ModelInfo] = await asyncio.to_thread(
        discover_models, config.models_dir
    )
    return [
        ModelResponse(
            name=m.name,
            path=str(m.path),
            size_bytes=m.size_bytes,
        )
        for m in models
    ]


# Global registry to hold active runners (simplified for single-user local API)
active_runners: dict[str, LocalLlamaRunner | None] = {}


@app.post("/chat/start")
async def start_chat(request: ChatStartRequest) -> StreamingResponse:
    """Start a chat session and stream the stdout using Server-Sent Events."""
    models: list[ModelInfo] = await asyncio.to_thread(
        discover_models, config.models_dir
    )
    model = next((m for m in models if m.name == request.model_name), None)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    # Handle concurrency and resource cleanup
    while (
        request.model_name in active_runners
        and active_runners[request.model_name] is None
    ):
        await asyncio.sleep(0.1)

    old_runner = active_runners.get(request.model_name)
    active_runners[request.model_name] = None

    if old_runner is not None:
        await old_runner.stop()

    runner = LocalLlamaRunner(
        llama_cli=config.llama_cli,
        bitnet_root=config.bitnet_root,
    )
    # Start process with default config for API
    # You can extend this endpoint to accept config parameters
    try:
        await runner.start(model, config=InferenceConfig(n_predict=512))
    except Exception:
        active_runners.pop(request.model_name, None)
        raise
    except BaseException:
        active_runners.pop(request.model_name, None)
        raise

    active_runners[request.model_name] = runner

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            async for chunk in runner.stream_stdout():
                # Server-Sent Events format
                yield f"data: {chunk}\n\n"
        finally:
            try:
                await runner.stop()
            finally:
                if active_runners.get(request.model_name) is runner:
                    active_runners.pop(request.model_name, None)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/chat/send")
async def send_chat_message(request: ChatSendRequest) -> dict[str, str]:
    """Send a message to an active chat session."""
    runner = active_runners.get(request.model_name)
    if not runner:
        raise HTTPException(status_code=404, detail="Active chat session not found")

    await runner.send_message(request.message)
    return {"status": "success", "message": "Message sent to process stdin"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
