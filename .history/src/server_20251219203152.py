#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FastAPI application entrypoint for VisionAI-ClipsMaster.
- Aggregates all API routers from src.api
- Adds performance middleware and permissive CORS
- Optionally integrates realtime endpoints if dependencies are available

Run:
  uvicorn src.server:app --host 0.0.0.0 --port 8000
"""
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from src.api import api_router
from src.api.middleware.performance_monitor import PerformanceMonitorMiddleware

from contextlib import asynccontextmanager

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    try:
        from src.realtime.fastapi_integration import initialize_realtime
        await initialize_realtime(app, prefix="/realtime")
        logger.info("Realtime endpoints initialized under /realtime")
    except Exception as e:
        # Realtime is optional; don't block the server start
        logger.warning(f"Realtime initialization skipped: {e}")
    yield

# Create FastAPI app
app = FastAPI(title="VisionAI-ClipsMaster API", version="1.2.0", lifespan=app_lifespan)

# Middlewares
app.add_middleware(PerformanceMonitorMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(api_router)


# Health check
@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


# Optional realtime integration


if __name__ == "__main__":
    try:
        import uvicorn

        uvicorn.run("src.server:app", host="0.0.0.0", port=8000, reload=False)
    except Exception as e:
        logger.error(f"Failed to start uvicorn: {e}")

