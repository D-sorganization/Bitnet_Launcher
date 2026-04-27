"""FastAPI server for BitNet Launcher."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from bitnet_launcher.config import BitnetConfig
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


@app.post("/chat/start")
async def start_chat(model_name: str) -> dict[str, str]:
    """Start a chat session for a specific model."""
    models: list[ModelInfo] = discover_models(config.models_dir)
    model = next((m for m in models if m.name == model_name), None)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    # TODO: Implement chat session management via API
    return {"status": "success", "message": f"Started session with {model_name}"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
