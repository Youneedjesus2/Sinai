# Title
Add escalation rule when approved service context is missing

## Problem
The system may answer too confidently when retrieval returns weak or empty context.

## Goal
Force human escalation or safe fallback when trustworthy context is insufficient.

## Why it matters
Prevents hallucinated service claims and improves trust.

## Acceptance Criteria
- if retrieval score below threshold, no direct answer is sent
- fallback message is used
- escalation flag created
- event logged in audit table
- tests added

## Out of scope
- changing vector DB
- changing summary logic