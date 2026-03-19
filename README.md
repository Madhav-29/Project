# Clinical Gap Intelligence

Enterprise-style clinical AI assistant for synthetic EHR data, patient-specific RAG, vector search, transparent rule-based gap detection, human review workflow, and OpenAI/Azure OpenAI synthesis.

This project uses synthetic data only. Do not use real PHI.

## Business Problem

Care managers, quality reviewers, coders, and revenue integrity teams often need to reconcile patient data across conditions, labs, vitals, medications, encounters, procedures, and documentation history. This project demonstrates how an assistant can answer patient-specific clinical operations questions while grounding responses in retrieved evidence, timeline events, and transparent rules.

## Architecture

```text
Clinician question
      |
      v
FastAPI /ask
      |
      v
PatientContextTool -> TimelineTool -> RetrieverTool -> ClinicalRulesTool
      |                  |              |                 |
      v                  v              v                 v
Synthetic profile   Timeline events   Hybrid RAG       Care/doc/risk gaps
      \____________________|______________|_________________/
                           v
                  AnswerGeneratorTool
                           |
                           v
                  SafetyValidatorTool
                           |
                           v
          Assistant answer + evidence + audit trail
```

## Data Flow

1. Synthea-style CSV files or bundled sample data are loaded.
2. Patient records are normalized into chronological timeline events.
3. Timeline events become clinical documents with metadata such as `patient_id`, `source_type`, `date`, `code`, `description`, and `category`.
4. Documents are chunked, embedded, and stored in a local JSON vector-store adapter.
5. `/ask` filters retrieval by `patient_id`, combines vector similarity with keyword matching, runs clinical rules, generates a grounded answer, validates it, and returns audit metadata.

## RAG Design

- Patient-specific retrieval always filters by `patient_id`.
- Hybrid retrieval combines vector similarity with keyword/document metadata matching.
- Supporting evidence is returned directly in the `/ask` response.
- The vector-store boundary is local today and can be replaced by FAISS, ChromaDB, or Azure AI Search later.

## LLM Orchestration

The assistant uses a clean custom orchestration loop inspired by multi-step agent patterns:

- `PatientContextTool`: loads synthetic patient profile.
- `TimelineTool`: builds timeline events.
- `RetrieverTool`: retrieves patient-specific evidence.
- `ClinicalRulesTool`: runs care gap, documentation, and revenue-quality rules.
- `AnswerGeneratorTool`: calls OpenAI or Azure OpenAI when configured.
- `SafetyValidatorTool`: checks grounding signals.
- `AuditLoggerTool`: records retrieval strategy, model status, fired rules, confidence, and latency.

When model credentials are not configured, `/ask` returns:

```text
AI Assistant summary unavailable. Configure model credentials to enable generated summaries.
```

## Rule Engine

Implemented transparent evidence-backed rules include:

- Diabetes HbA1c monitoring
- Diabetes uncontrolled HbA1c >= 8
- Diabetes retinal/eye exam
- Hypertension BP monitoring
- CKD eGFR monitoring
- Obesity/BMI follow-up
- COPD follow-up/spirometry
- Older adult annual wellness visit
- Medication review due
- Chronic condition not reassessed in current year
- Revenue and quality recapture risk signals

## Human Review Workflow

Healthcare-appropriate review endpoints support marking a gap as:

- `needs_review`
- `accepted`
- `dismissed`

Reviewer, note, timestamp, patient ID, and gap ID are stored in a local JSON audit log under `data/audit/`.

## Setup

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

## Environment Variables

```env
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_DEPLOYMENT_NAME=
AZURE_OPENAI_API_VERSION=2024-10-21
```

## Run Locally

```bash
python scripts/build_index.py
uvicorn app.api.main:app --reload
```

Swagger API: `http://localhost:8000/docs`
ReDoc: `http://localhost:8000/redoc`

Optional Streamlit UI:

```bash
streamlit run frontend/streamlit_app.py
```

## API Examples

```bash
curl http://localhost:8000/health
curl http://localhost:8000/patients
```

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"patient_id":"p001","question":"What care gaps exist for this patient?","data_source":"synthea"}'
```

```bash
curl -X POST http://localhost:8000/patients/p001/reviews \
  -H "Content-Type: application/json" \
  -d '{"gap_id":"care_gap:Diabetes HbA1c monitoring due","status":"needs_review","reviewer":"quality_reviewer","note":"Review in chart prep."}'
```

## Synthea Data

Place generated Synthea CSV files in `data/synthea/csv`.

Expected files include:

- `patients.csv`
- `conditions.csv`
- `observations.csv`
- `medications.csv`
- `encounters.csv`
- `procedures.csv`
- `careplans.csv`

If Synthea data is absent, bundled sample data is used.

## Evaluation

Small evaluation prompts live in `evals/questions.json`. Tests cover:

- Synthea/sample loading
- Timeline creation
- Rule detection
- Patient-specific retrieval
- `/ask` response contract
- Grounding fallback behavior
- Human review audit events

Run:

```bash
pytest
```

## Docker

```bash
cp .env.example .env
docker compose up --build
```

API: `http://localhost:8000/docs`
Frontend: `http://localhost:8501`

## Screenshots

Add screenshots here:

- Swagger `/ask` request and response
- Streamlit assistant question flow
- Evidence and audit trail tabs
- Review workflow endpoint

## Azure Deployment Roadmap

- Replace local vector JSON with Azure AI Search.
- Persist normalized data and review events in Azure PostgreSQL.
- Add Azure Container Apps or App Service deployment.
- Add managed identity and Key Vault for secrets.
- Add structured telemetry with Application Insights.
- Add evaluator jobs for retrieval relevance and groundedness.

## Limitations

- Not a medical device.
- Synthetic data only.
- Rule logic is transparent but simplified.
- LLM output is grounded by retrieved context and rules but still requires professional review.
- No real PHI should be stored or processed.

## Future Improvements

- FHIR ingestion and terminology normalization.
- Measure-specific logic for HEDIS, CMS Stars, RAF, and payer contracts.
- Role-based access control and tenant isolation.
- Full LangGraph implementation for stateful orchestration.
- Richer evaluation harness for completeness, retrieval relevance, and unsupported-claim detection.
