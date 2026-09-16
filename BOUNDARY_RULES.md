# Keyword & Boundary Rule Documentation

## Source

The keyword master list (`backend/data/keywords.json`) was built from a curated
sustainability/ESG terminology reference covering 23 thematic categories:

1. Core ESG Terms
2. Climate Change & Global Warming
3. Carbon & Emissions
4. Sustainability — General
5. Circular Economy & Waste
6. Biodiversity & Nature
7. Water & Oceans
8. Energy Transition
9. Sustainable Food & Agriculture
10. Regulations & Reporting Frameworks
11. Sustainable Finance & Investing
12. Corporate Strategy & Governance
13. Industry & Sector Decarbonization
14. Just Transition & Social Equity
15. Social & Labor Rights
16. Governance & Business Ethics
17. Climate Tech & Innovation
18. Green Buildings & Urban Sustainability
19. Supply Chain & Procurement
20. Geopolitical & Regional ESG
21. ESG Data, Ratings & Disclosure
22. Climate Risk & Resilience
23. Communications & Reporting Terms

**Total: 1,627 unique keywords/phrases.**

## Boundary Rule Logic

A request is classified **in-scope** if either of the following is true:

1. **Keyword match rule**: the request text contains one or more terms from
   the keyword list (case-insensitive, word-boundary matched to avoid partial
   matches like "esg" inside an unrelated word).
   - 3+ matches -> high confidence
   - 1-2 matches -> medium confidence
   - 0 matches -> low confidence, escalates to rule 2

2. **LLM fallback rule**: for requests with zero keyword matches, the fast
   model (Gemma 2 9B) makes a binary judgment on whether the request relates
   to environment, sustainability, ESG, climate, energy, emissions, or
   corporate sustainability compliance — catching paraphrased requests a
   fixed keyword list would miss.

A request is classified **out-of-scope** if the LLM fallback also returns NO.

## Response-Side Boundary Check

Boundary enforcement is not just applied to the incoming request — every
generated response is re-checked against the same keyword classifier
(`rules_engine.py`, check `response_stays_in_scope`) before being returned,
preventing scope drift during generation.

## Example Keywords by Category (abridged)

| Category | Sample Keywords |
|---|---|
| Core ESG Terms | ESG, ESG investing, ESG reporting, ESG ratings, ESG disclosure |
| Carbon & Emissions | net zero, carbon neutral, Scope 1/2/3 emissions, GHG emissions |
| Regulations & Reporting | CSRD, ESRS, BRSR, TNFD, SBTi |
| Water & Oceans | water stewardship, water scarcity, water stress |
| Biodiversity & Nature | biodiversity loss, species extinction, nature positive |

Full list: see `backend/data/keywords.json`.

## Configured Out-of-Scope Examples (used in testing)

- General creative writing ("write me a poem about my cat")
- Unrelated factual queries ("what time zone is Tokyo in")
- Entertainment/sports news
- Coding help unrelated to sustainability tooling
- Weather/travel queries

See `SAMPLE_INPUTS_OUTPUTS.md` and `eval/test_cases.json` for the full labeled
test set (8 in-scope, 7 out-of-scope) and 100% measured accuracy.
