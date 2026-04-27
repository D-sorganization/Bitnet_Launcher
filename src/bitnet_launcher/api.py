"""FastAPI server for BitNet Launcher."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from bitnet_launcher.config import BitnetConfig, InferenceConfig
from bitnet_launcher.models import ModelInfo, discover_models

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

config = BitnetConfig()


class ModelResponse(BaseModel):
    """API response model for a discovered BitNet model."""

    name: str
    path: str
    size_bytes: int


@app.get("/models")
async def list_models() -> list[ModelResponse]:
    """List all locally installed BitNet models."""
    models: list[ModelInfo] = discover_models(config.models_dir)
    return [
        ModelResponse(
            name=m.name,
            path=str(m.path),
            size_bytes=m.size_bytes,
        )
        for m in models
    ]


from fastapi.responses import StreamingResponse

from bitnet_launcher.runners import LocalLlamaRunner

# Global registry to hold active runners (simplified for single-user local API)
active_runners: dict[str, LocalLlamaRunner] = {}


@app.post("/chat/start")
async def start_chat(model_name: str) -> StreamingResponse:
    """Start a chat session and stream the stdout using Server-Sent Events."""
    models: list[ModelInfo] = discover_models(config.models_dir)
    model = next((m for m in models if m.name == model_name), None)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    runner = LocalLlamaRunner(
        llama_cli=config.llama_cli,
        bitnet_root=config.bitnet_root,
    )
    # Start process with default config for API
    # You can extend this endpoint to accept config parameters
    await runner.start(model, config=InferenceConfig(n_predict=512))
    active_runners[model_name] = runner

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            async for chunk in runner.stream_stdout():
                # Server-Sent Events format
                yield f"data: {chunk}\n\n"
        finally:
            await runner.stop()
            active_runners.pop(model_name, None)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/chat/send")
async def send_chat_message(model_name: str, message: str) -> dict[str, str]:
    """Send a message to an active chat session."""
    runner = active_runners.get(model_name)
    if not runner:
        raise HTTPException(status_code=404, detail="Active chat session not found")

    await runner.send_message(message)
    return {"status": "success", "message": "Message sent to process stdin"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
