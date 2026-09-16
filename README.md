# ZenAI Agent

A prototype AI orchestration agent for Zenlynx Technology's enterprise sustainability platform.
Classifies requests, enforces an environment/sustainability scope boundary, routes to the
right AI/ML model, retrieves cited context via RAG, validates outputs against rules, and
exposes a review dashboard showing the full decision trail.

## Architecture

```
Request -> Scope Classifier (keyword + LLM fallback) -> [reject if out-of-scope]
        -> Model Router -> RAG Retriever (Pinecone) -> Groq LLM
        -> Rules Engine (validation) -> Response + full audit trail -> Supabase log
```

See `DESIGN_NOTE.md` for full architecture rationale.

## Tech Stack (100% free tier)

| Component | Choice |
|---|---|
| Fast LLM | Groq — Gemma 2 9B |
| Reasoning LLM | Groq — Llama 3.3 70B |
| Vector DB (RAG) | Pinecone (free tier) |
| Database | Supabase (Postgres, free tier) |
| Embeddings | sentence-transformers (local, free) |
| Backend | FastAPI |
| Frontend | React (deployed on Netlify) |
| Backend hosting | Render (free tier) |
| CI/CD | GitHub Actions |

## Setup

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r ../requirements.txt
cp ../.env.example ../.env   # then fill in your real keys
python app.py
```

API runs at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### 2. Required accounts (all free)

- **Groq**: console.groq.com -> API Keys
- **Pinecone**: app.pinecone.io -> API Keys
- **Supabase**: supabase.com -> new project -> Settings -> Data API / API Keys / Database

Fill these into `.env` (see `.env.example` for the full list).

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

### 4. Run the evaluation suite

```bash
cd backend
python eval/run_eval.py
```

## API Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/chat` | Ask a sustainability question, get a cited answer |
| POST | `/analyze-document` | Upload a document for sustainability analysis |
| GET | `/regulatory-radar/run` | Run the full regulatory monitoring pipeline |
| GET | `/dashboard/requests` | Review interface data feed |

## Sample Requests

**In-scope:**
```json
POST /chat
{"message": "What are our Scope 1 and Scope 2 emissions for this quarter?"}
```
-> classified in-scope, routed to reasoning model, RAG-cited answer returned.

**Out-of-scope:**
```json
POST /chat
{"message": "Write me a poem about my cat"}
```
-> rejected immediately with a clear boundary message, no model call made.

See `eval/test_cases.json` for 15 labeled examples (8 in-scope, 7 out-of-scope).

## Boundary Rules

Scope detection uses a 1,627-keyword list across 23 sustainability categories
(`data/keywords.json`), sourced from ESG/climate/carbon terminology. See
`DESIGN_NOTE.md` for the full boundary-rule documentation.

## Deployment

- **Frontend**: Netlify, auto-deployed from `main` via GitHub Actions
  (`.github/workflows/frontend-deploy.yml`)
- **Backend**: Render, connected directly to this GitHub repo for auto-deploy on push
  (Render's own GitHub integration — configured in the Render dashboard)
- **CI**: GitHub Actions runs the eval suite and a syntax check on every push
  (`.github/workflows/backend-deploy.yml`)

## Project Structure

```
backend/
  app.py                 FastAPI entrypoint
  config.py              env/settings loader
  scope_classifier.py    boundary/keyword scope detection
  model_router.py        request-type -> model routing logic
  orchestrator.py         ties everything together
  rules_engine.py         output validation
  ingestion.py            document loading + chunking
  embeddings.py            Pinecone embedding + upsert
  retriever.py             Pinecone RAG retrieval
  regulatory_radar.py      ingest -> filter -> tag -> analyze -> alert pipeline
  models/groq_client.py    Groq API wrapper
  db/                      Supabase/Postgres models + connection
  data/                    keywords.json, mock documents, mock regulatory feed
  eval/                    labeled test cases + evaluation script
frontend/                  React dashboard
.github/workflows/         CI/CD pipelines
```
