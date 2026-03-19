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
    description="Live synthetic-data clinical AI prototype for care gap, documentation gap, and quality risk review.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
