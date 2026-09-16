# Sample In-Scope and Out-of-Scope Inputs/Outputs

## Example 1: In-Scope Request (AI Chat)

**Input:**
```
POST /chat
{"message": "What are our Scope 1 and Scope 2 emissions for this quarter?"}
```

**Scope Check:** IN-SCOPE
**Method:** keyword_match (confidence: medium)
**Matched keywords:** scope 1 emissions, scope 2 emissions
**Matched categories:** Carbon & Emissions
**Request type:** ai_chat
**Model selected:** groq_reasoning (Llama 3.3 70B)
**Reason for model selection:** "General sustainability Q&A needs contextual
reasoning over retrieved (RAG) sources, not just classification."
**Retrieved sources:** sample_sustainability_report.txt
**Validation status:** PASSED (response stayed in-scope, cited a source, non-empty)
**Action taken:** answered


## Example 2: Out-of-Scope Request (AI Chat)

**Input:**
```
POST /chat
{"message": "Write me a poem about my cat"}
```

**Scope Check:** OUT-OF-SCOPE
**Method:** keyword_match (confidence: low)
**Matched keywords:** none
**Request type:** N/A — rejected before classification
**Model selected:** none — no model was called
**Reason:** "No sustainability/environment keywords detected in the request."
**Final response:**
> "This request appears to be outside ZenAI's environment & sustainability
> scope. ZenAI only handles questions related to ESG, climate, emissions,
> energy, waste, biodiversity, water, or corporate sustainability compliance.
> Please rephrase your request within that scope, or contact general support
> for other topics."
**Action taken:** rejected


## Example 3: In-Scope Request (Regulatory Monitoring)

**Input:** (from mock regulatory feed)
```
Title: "EU Finalizes CSRD Phase 2 Reporting Requirements for Mid-Cap Companies"
```

**Scope Check:** RELEVANT
**Matched keywords:** biodiversity, corporate sustainability, corporate
sustainability reporting directive, csrd
**Pipeline stage:** Ingest -> Filter -> Tag -> AI Impact Analysis -> Alert generated
**Output:** Structured alert + LinkedIn-style post generated using the
supplied regulatory-alert prompt template.


## Example 4: Out-of-Scope Item (Regulatory Monitoring — correctly filtered)

**Input:** (from mock regulatory feed)
```
Title: "Local Football League Announces New Season Schedule"
```

**Scope Check:** FILTERED OUT (not relevant)
**Matched keywords:** none
**Output:** No alert generated, no AI Impact Analysis run, no LinkedIn post
generated — pipeline correctly stops after the filter stage.


## Full Evaluation Results

15 labeled test cases (8 in-scope, 7 out-of-scope) run via `eval/run_eval.py`:
**Result: 100% accuracy (15/15 correct)**. Full results in `eval/test_cases.json`
and reproducible by running `python eval/run_eval.py` from the `backend/` directory.
