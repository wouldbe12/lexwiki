"""Prompt templates for document classification."""

CLASSIFY_SYSTEM = "You are a legal document classifier. Respond only with valid JSON."

CLASSIFY_PROMPT = """\
Analyze this legal document and classify it.

Document excerpt (beginning):
---
{excerpt_head}
---

Document excerpt (ending):
---
{excerpt_tail}
---

Respond with ONLY a JSON object (no markdown fences):
{{
  "type": "contract" | "statute" | "case_law" | "memo" | "regulation" | "filing" | "other",
  "title": "Human-readable title for this document",
  "jurisdiction": "Jurisdiction if identifiable, else 'unknown'",
  "parties": ["Party A", "Party B"],
  "effective_date": "YYYY-MM-DD or null",
  "subject_areas": ["area1", "area2"],
  "confidence": 0.0
}}

Rules:
- "type" must be one of: contract, statute, case_law, memo, regulation, filing, other
- "parties" should be an empty list if not a contract or filing
- "subject_areas" should contain 1-3 legal topics (e.g. "employment", "data protection", "corporate governance")
- "confidence" is your confidence in the classification from 0.0 to 1.0
"""
