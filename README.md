# Clinical AI Platform

Full-stack Clinical Gap Intelligence platform for synthetic patient data, transparent care-gap rules, local retrieval, and optional OpenAI or Azure OpenAI synthesis.

This repository uses synthetic data only. Do not use real PHI.

## Architecture

```text
Synthea CSV / sample CSV
        |
        v
Ingestion -> Normalization -> Patient Timeline
        |                         |
        |                         v
        |                  Rule Engine
        |                         |
        v                         v
Timeline Documents -> Chunking -> Embeddings -> Local Vector Index
                                             |
                                             v
                                   Hybrid Retriever
                                             |
                                             v
FastAPI APIs + Live Status <------ RAG Orchestrator ---- OpenAI/Azure OpenAI
    |
    v
Simple Streamlit Live UI
```

## What It Does

- Ingests Synthea-style CSV files or bundled sample data.
- Builds chronological patient timelines from conditions, labs, vitals, medications, encounters, procedures, and care plans.
- Detects care gaps, documentation gaps, and revenue/quality risks with evidence-backed rules.
- Indexes timeline evidence into a local vector store.
- Retrieves evidence for patient questions.
- Uses OpenAI or Azure OpenAI when configured for grounded synthesis.
- Exposes FastAPI endpoints and a simple live Streamlit analyst UI.
- Provides `/live/overview` for operational status, cohort count, index readiness, and recent analysis metadata.

## Setup

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

## Run Locally

Build the local evidence index:

```bash
python scripts/build_index.py
```

Start the backend:

```bash
uvicorn app.api.main:app --reload
```

Start the frontend in another terminal:

```bash
streamlit run frontend/streamlit_app.py
```

Backend: `http://localhost:8000`
Frontend: `http://localhost:8501`
API docs: `http://localhost:8000/docs`

The frontend is designed as a concise clinical operations dashboard: select a patient, ask a clinical question, run analysis, and review findings across structured tabs.

## Synthea Data

Place Synthea CSV files in `data/synthea/csv`.

Expected files include:

- `patients.csv`
- `conditions.csv`
- `observations.csv`
- `medications.csv`
- `encounters.csv`
- `procedures.csv`
- `careplans.csv`
- `claims.csv` if available

See `scripts/generate_synthea_instructions.md` for generation steps. If Synthea data is absent, the app uses bundled synthetic sample data.

## API Examples

```bash
curl http://localhost:8000/health
curl http://localhost:8000/live/overview
curl http://localhost:8000/patients
```

```bash
curl -X POST http://localhost:8000/analyze-patient \
  -H "Content-Type: application/json" \
  -d '{"patient_id":"p001","question":"Identify care gaps, documentation gaps, and revenue risks","use_llm":false}'
```

## Docker

```bash
cp .env.example .env
docker compose up --build
```

Backend runs on port `8000`; Streamlit runs on port `8501`.

## Tests

```bash
pytest
```

## Screenshots

Add screenshots here after running the Streamlit app:

- Clinical Gap Intelligence dashboard header and KPI cards
- Sidebar cohort filters and AI Assistant controls
- Care Gap Analysis, Documentation Review, and Revenue & Quality Risk tabs
- Evidence Summary and Patient Timeline tabs
- FastAPI docs

## Limitations

- This is not a medical device.
- Rules are intentionally transparent but simplified.
- Local vector search uses deterministic hash embeddings by default for offline operation.
- LLM synthesis is optional and never used as the sole source of truth.
- Clinical, coding, and quality outputs require human validation.

## Production Roadmap

- Persist normalized data in Postgres.
- Replace local vector JSON with FAISS, Chroma, or Azure AI Search.
- Add FHIR ingestion and terminology normalization.
- Add measure-specific logic for HEDIS, CMS Stars, RAF, and payer contracts.
- Add role-based access control, audit logs, and tenant isolation.
- Add background indexing jobs and observability dashboards.
- Add evaluation sets for retrieval quality and rule precision.
