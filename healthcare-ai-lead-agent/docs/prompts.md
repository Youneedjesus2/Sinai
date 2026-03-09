# Prompt Design and Management
Healthcare AI Lead Intake Agent

---

# 1. Purpose

This document defines how prompts are written, reviewed, versioned, and tested.

Prompts are part of the product logic and must be treated like code.

A prompt change can alter:
- system behavior
- safety boundaries
- tone
- retrieval usage
- escalation behavior

Because of this, prompt changes require review and evaluation.

---

# 2. Prompt Design Principles

Prompts should:

- be clear and specific
- define system role and boundaries
- describe what the model must do
- describe what the model must never do
- prefer structured outputs over free-form text
- define fallback behavior when context is weak
- avoid hidden business logic outside reviewed prompt files

---

# 3. Prompt Categories

## System Prompts
High-level instructions that define the model’s role and safety boundaries.

Examples:
- the system is a lead intake assistant
- the system does not provide medical advice
- the system must escalate rather than guess

---

## Task Prompts
Prompts used for a specific operation.

Examples:
- classify message intent
- extract intake fields
- generate lead summary
- create channel-specific reply

---

## Channel Prompts
Instructions specific to communication channel.

Examples:
- SMS should be short and conversational
- email should be more formal and include an intro when appropriate

---

## Retrieval-Conditioned Prompts
Prompts that depend on retrieved approved context.

These prompts should instruct the model to:
- use only retrieved approved context
- avoid unsupported claims
- return fallback when context is insufficient

---

# 4. Prompt Storage

Prompts should be stored in version-controlled files, not buried inside application logic.

Recommended structure:

prompts/
- system/
- tasks/
- channels/
- templates/

Example:
- prompts/system/lead_intake_assistant.md
- prompts/tasks/classify_intent.md
- prompts/tasks/generate_summary.md
- prompts/channels/sms_reply.md
- prompts/channels/email_reply.md

---

# 5. Prompt Versioning

Each major prompt should have:

- prompt name
- version number
- last modified date
- owner
- linked eval results if behavior changed

Example metadata:

- prompt: classify_intent
- version: v1
- owner: backend
- last_updated: 2026-03-09

---

# 6. Prompt Rules

Every prompt must define:

- role
- allowed scope
- forbidden actions
- expected output format
- fallback behavior

Example rule:
If the system does not have enough reliable approved context, it must not guess.

---

# 7. Prompt Review Requirements

A prompt change should not be merged unless:

- the reason for change is documented
- relevant evals are run
- reviewers understand behavior impact
- fallback behavior is preserved
- safety boundaries are still enforced

---

# 8. Prompt Testing

Prompt behavior should be tested using:

- eval datasets
- manual review of sample outputs
- structured output validation
- edge case prompts
- unsafe prompt attempts

---

# 9. Anti-Patterns

Avoid:

- giant prompts that mix multiple jobs
- prompts with hidden product logic
- prompts that allow unsupported improvisation
- prompts that silently change output structure
- prompts that skip fallback rules

---

# 10. Initial Prompt Set for MVP

The MVP will likely need these prompts:

- lead intake assistant system prompt
- intent classification prompt
- intake extraction prompt
- retrieval-grounded answer prompt
- SMS reply rendering prompt
- email reply rendering prompt
- lead summary generation prompt
- escalation recommendation prompt

---

# 11. Core Prompt Rule

The model must not present unsupported claims as facts.

If context is missing, it should use a safe fallback or escalate to a human.