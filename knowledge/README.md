# Knowledge Directory

This directory contains the **approved RAG source documents** for the Healthcare AI Lead Intake Agent.

## What belongs here

Only documents explicitly approved by the agency should be placed here. Approved sources include:

- Agency service descriptions
- Approved FAQ documents
- Scheduling rules and availability policies
- Intake requirements and eligibility criteria
- Coverage area and service area notes
- Approved response templates

## What does NOT belong here

- Clinical guidelines or medical reference material
- Documents not reviewed and approved by the agency
- Any file containing PHI or PII
- Unapproved third-party content

## How it works

All `.md` and `.txt` files in this directory are ingested by the retrieval pipeline (LlamaIndex + pgvector). The system uses semantic search to find relevant context before generating a reply. If no trusted context is found above the confidence threshold, the system escalates to a human instead of guessing.

## Adding new documents

1. Place the file (`.md` or `.txt`) in this directory
2. Restart the API or trigger a re-index to make the content available
3. Run evals to verify retrieval quality before deploying to production

## File naming

Use descriptive, lowercase, hyphenated filenames:
- `home-care-services.md`
- `scheduling-policy.md`
- `service-areas.md`
- `intake-faq.md`
