# Healthcare AI Lead Intake Agent

## Purpose
This product helps healthcare agencies respond to new inbound leads across form, SMS, and email, answer service questions using approved knowledge sources, collect structured intake details, schedule consultations, and summarize conversations for human staff.

## Non-Goals
This system does not provide diagnosis, treatment recommendations, medical advice, or guaranteed eligibility/coverage decisions.

## Core Principles
- Approved-source answers only
- Structured outputs before user-facing text
- Human escalation over guessing
- Auditability over convenience
- Small safe changes over large unmeasured changes

## High-Level Architecture
1. Inbound channel receives lead
2. Message normalized into common schema
3. Retrieval gets approved context
4. LLM produces structured output
5. Business rules validate output
6. Response rendered to channel
7. Scheduling and summary actions run
8. Logs and audit records stored

## Source of Truth
The system may answer only from:
- approved agency service docs
- approved policy docs
- approved FAQs
- approved scheduling rules
- approved staff-configured templates

## Safe Failure Rule
If the system cannot retrieve trustworthy context, it must say:
“I don’t have enough reliable information to answer that right now.”

## Change Rules
The following require review and updated evals:
- prompt changes
- model changes
- retrieval changes
- chunking/embedding changes
- tool schema changes
- scheduling logic changes
- channel template changes
- logging/retention changes

## Required Before Merge
- linked issue
- tests updated
- eval results attached
- security/privacy impact note
- rollback plan
- docs updated if behavior changed

## Local Development
[add setup instructions]

## Testing
[add commands]

## Evals
See `evals/README.md`

## Security
See `security/threat-model.md` and `security/data-governance.md`