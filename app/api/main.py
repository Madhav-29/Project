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
    title="Clinical Gap Intelligence API",
    version="0.1.0",
    summary="Swagger-first Clinical AI Assistant for patient-specific gap intelligence.",
    description=(
        "Enterprise-style Clinical AI Assistant for synthetic EHR data. Use Swagger to select a patient, ask a "
        "clinical question through `/ask`, and review grounded care gap, documentation, revenue-quality, evidence, "
        "and timeline outputs. This environment is for synthetic data only."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "Assistant",
            "description": "Natural-language clinical assistant endpoints backed by RAG, rules, timeline, and model synthesis.",
        },
        {
            "name": "Patients",
            "description": "Synthetic patient cohort and patient context endpoints.",
        },
        {
            "name": "Analysis",
            "description": "Structured care gap and quality-risk analysis endpoints.",
        },
        {
            "name": "Data Operations",
            "description": "Synthetic data ingestion and evidence-index operations.",
        },
        {
            "name": "System",
            "description": "Health and runtime status endpoints.",
        },
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
