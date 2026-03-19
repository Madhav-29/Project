# Clinical AI Platform

An enterprise-style clinical AI assistant using synthetic EHR data, RAG, vector search, rule-based gap detection, and OpenAI/Azure OpenAI synthesis.

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
Swagger / FastAPI Docs <------ FastAPI APIs + Assistant Status
                                      |
                                      v
                         RAG Orchestrator ---- OpenAI/Azure OpenAI
```

## What It Does

- Ingests Synthea-style CSV files or bundled sample data.
- Builds chronological patient timelines from conditions, labs, vitals, medications, encounters, procedures, and care plans.
- Detects care gaps, documentation gaps, and revenue/quality risks with evidence-backed rules.
- Indexes timeline evidence into a local vector store.
- Retrieves evidence for patient questions.
- Uses OpenAI or Azure OpenAI when configured for grounded synthesis.
- Exposes a Swagger-first Clinical Gap Intelligence Assistant at `/docs`.
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

Backend: `http://localhost:8000`
Swagger assistant: `http://localhost:8000/docs`
ReDoc: `http://localhost:8000/redoc`

Use Swagger as the primary interface: open `/docs`, expand `POST /ask`, choose **Try it out**, submit a synthetic patient ID and question, then review the assistant answer, care gaps, documentation findings, revenue-quality risks, evidence, and timeline summary in the response.

Optional Streamlit UI:

```bash
streamlit run frontend/streamlit_app.py
```

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
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"patient_id":"p001","question":"What care gaps exist for this patient?","data_source":"synthea"}'
```

```bash
curl -X POST http://localhost:8000/analyze-patient \
  -H "Content-Type: application/json" \
  -d '{"patient_id":"p001","question":"Identify care gaps, documentation gaps, and revenue risks"}'
```

## Docker

```bash
cp .env.example .env
docker compose up --build
```

Backend runs on port `8000`. The Swagger assistant is available at `http://localhost:8000/docs`.

## Tests

```bash
pytest
```

## Screenshots

Add screenshots here after running the API docs:

- Swagger `POST /ask` request example
- Swagger `POST /ask` assistant response
- FastAPI endpoint groups for Assistant, Patients, Analysis, Data Operations, and System

## Limitations

- This is not a medical device.
- Rules are intentionally transparent but simplified.
- Local vector search uses deterministic hash embeddings by default for offline operation.
- OpenAI or Azure OpenAI synthesis is grounded by retrieved evidence and rule outputs.
- Clinical, coding, and quality outputs require human validation.

## Production Roadmap

- Persist normalized data in Postgres.
- Replace local vector JSON with FAISS, Chroma, or Azure AI Search.
- Add FHIR ingestion and terminology normalization.
- Add measure-specific logic for HEDIS, CMS Stars, RAF, and payer contracts.
- Add role-based access control, audit logs, and tenant isolation.
- Add background indexing jobs and observability dashboards.
- Add evaluation sets for retrieval quality and rule precision.
