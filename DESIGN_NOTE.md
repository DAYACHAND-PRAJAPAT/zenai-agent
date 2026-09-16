# ZenAI Agent — Design Note

## 1. Overview

ZenAI is the AI orchestration layer for Zenlynx Technology's sustainability platform.
It receives a user request, determines whether it falls within the environment &
sustainability scope, routes in-scope requests to the appropriate AI/ML model,
retrieves supporting evidence via RAG, validates the generated response against
rules, and returns a fully auditable answer.

## 2. Architecture

The system follows the four-layer architecture specified in the assignment:

**Data Layer** — `data/keywords.json` holds 1,627 sustainability keywords across 23
categories (ESG, climate, carbon/emissions, biodiversity, water, energy transition,
regulations, supply chain, etc.), extracted from a curated ESG terminology reference.
`data/mock_documents/` and `data/mock_regulatory_feed.json` simulate enterprise
reports and regulatory news for testing without needing paid data feeds.

**AI Engine** — Two Groq-hosted LLMs cover the two model roles the assignment
specifies: Gemma 2 9B for fast classification/extraction/scope-detection, and
Llama 3.3 70B for reasoning, analysis, and impact assessment (the role
originally suggested for Claude — substituted with a free-tier equivalent per
project constraints). A placeholder ML model slot exists for anomaly
detection/forecasting on numerical sustainability data.

**RAG + Rules Engine** — `retriever.py` queries a Pinecone vector index (embedded
with a free local sentence-transformer model) for the top-k relevant document
chunks, attaching source citations. `rules_engine.py` then validates every
generated response against four checks: (1) the response itself stays within
scope, (2) the originating request was in-scope, (3) claims are backed by at
least one citation or explicitly admit a knowledge gap, (4) the response is
non-empty and substantive.

**ZenAI Orchestrator** — `orchestrator.py` is the central coordinator: it calls
the scope classifier first (short-circuiting immediately on out-of-scope
requests, before any model cost is incurred), then classifies request type,
routes to the correct model(s), executes RAG retrieval + generation, runs
rules validation, and returns a structured result with the full decision
trail attached.

## 3. Boundary Setting (Scope Enforcement)

Boundary setting uses a two-stage approach:

1. **Keyword/topic matching** (primary, deterministic, free, instant): the
   request text is scanned against the 1,627-keyword list. Three or more
   matches yield high confidence; one or two yield medium confidence; zero
   matches yield low confidence and trigger stage 2.
2. **LLM fallback** (secondary, for ambiguous phrasing that doesn't hit an
   exact keyword — e.g. "how do I cut my factory's electricity bill"): the
   fast model makes a binary in/out-of-scope judgment.

This two-stage design keeps the common case (clear keyword signal) essentially
free and instant, while still handling paraphrased or indirect requests that a
pure keyword list would miss.

Out-of-scope requests are rejected immediately with a clear boundary message
and never reach the LLM generation step, satisfying the assignment's
requirement to "reject, redirect, or request clarification" without wasting
model calls.

## 4. Model Routing Logic

| Request Type | Model(s) Used | Reason |
|---|---|---|
| AI Chat | Reasoning model (Llama 3.3 70B) | General sustainability Q&A needs contextual reasoning over RAG context, not just classification |
| Document Analysis | Fast model + Reasoning model | Fast model extracts key data points; reasoning model produces the analysis/impact summary |
| Regulatory Monitoring | Fast model + Reasoning model | Fast model tags/filters incoming content; reasoning model analyzes business/environmental impact |
| Anomaly/Forecast | ML model | Statistical/numerical tasks are better suited to a dedicated model than an LLM |

Every routing decision is logged with its reasoning string, directly
satisfying the dashboard's "model selected" + "reason for model selection"
requirement.

## 5. Regulatory Radar

Implements the exact pipeline specified: **Ingest → Filter → Apply Boundary
Rules → Tag → AI Impact Analysis → Output**. The mock regulatory feed (5 items,
mixing real sustainability regulations like CSRD/BRSR updates with clearly
unrelated news like sports and product launches) is filtered through the same
scope classifier used for chat requests, ensuring consistent boundary logic
across the whole system. Relevant items get an AI-generated impact analysis,
a structured alert, and a LinkedIn-style post generated from the supplied
prompt template.

## 6. Validation & Evaluation

`eval/run_eval.py` runs 15 labeled test cases (8 in-scope, 7 out-of-scope)
against the scope classifier and achieved **100% accuracy** in testing. This
script also runs automatically in GitHub Actions on every push, catching
scope-detection regressions before deployment.

## 7. Deployment Architecture

Given Netlify's serverless/static-hosting model can't run a persistent FastAPI
server or maintain SQLite state between requests, the system is split:
Netlify hosts the React dashboard, Render hosts the FastAPI backend
(persistent server, needed for Pinecone/Groq/Supabase calls), and Supabase
provides a production-grade Postgres database. GitHub Actions runs tests and
syntax checks on every push; Render and Netlify each auto-deploy from the
same `main` branch via their native GitHub integrations.

## 8. Known Limitations (Prototype Scope)

- The ML anomaly-detection/forecasting model is stubbed as a routing target
  but not yet implemented with real historical data — out of scope for a
  3-week prototype without an available anomaly dataset.
- The keyword list, while extensive (1,627 terms), is English-only.
- Regulatory ingestion uses a mock feed rather than a live news API to keep
  the project fully free.
