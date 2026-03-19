from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from app.api.routes import router  # noqa: E402
from app.observability.logging_config import configure_logging  # noqa: E402

configure_logging()

app = FastAPI(
    title="Clinical AI Platform",
    version="0.1.0",
    description="Clinical Gap Intelligence API for care gap, documentation, evidence, and quality risk workflows.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
