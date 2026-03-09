# Architecture

## Purpose

This system helps healthcare agencies handle inbound leads from forms, SMS, and email by automating first-response communication, answering questions using approved agency information, collecting structured intake details, scheduling consultation calls, and creating summaries for staff.

This system is **not** intended to diagnose, treat, or provide medical advice. Its job is to support lead intake and scheduling, then hand off to a real person when needed.

---

Lead → API → Orchestrator → RAG → LLM
         ↓
      Scheduler
         ↓
      Calendar
         ↓
      Dashboard

## Core Design Principles

- Use approved agency information as the source of truth
- Prefer structured outputs over free-form AI text
- Escalate to a human instead of guessing
- Keep channel logic separate from business logic
- Log important actions for debugging and auditability
- Minimize sensitive data storage
- Design every step so failures are visible and recoverable

---

## Components

### 1. Next.js Dashboard
The internal staff dashboard.

**Responsibilities**
- View leads
- View conversation history
- View consultation schedule
- View AI-generated summaries
- View escalation flags and failures
- Track lead status from first contact to scheduled call

---

### 2. FastAPI Backend
The main application server.

**Responsibilities**
- Receive inbound form, SMS, and email events
- Normalize inbound data into a common format
- Run business logic
- Call retrieval and AI services
- Trigger scheduling actions
- Store leads, messages, summaries, and logs
- Expose API routes for the dashboard

---

### 3. Postgres / Supabase
The primary system database.

**Responsibilities**
- Store leads
- Store messages
- Store appointment records
- Store summaries
- Store audit logs
- Store agency settings, templates, and approved knowledge source metadata

---

### 4. pgvector
Vector search extension attached to Postgres.

**Responsibilities**
- Store embeddings for approved documents
- Support semantic search for RAG retrieval

---

### 5. LlamaIndex
The retrieval and document pipeline layer.

**Responsibilities**
- Ingest approved agency documents
- Chunk documents into smaller searchable pieces
- Build retrieval pipelines
- Return relevant context for answering lead questions

---

### 6. OpenAI Responses API
The language model layer.

**Responsibilities**
- Interpret inbound lead messages
- Produce structured outputs
- Generate safe channel-specific replies
- Summarize conversations for staff
- Decide whether follow-up questions, scheduling, or escalation are needed

---

### 7. Twilio
Messaging provider for SMS.  
Future voice support may also be routed through Twilio.

**Responsibilities**
- Send SMS messages
- Receive inbound SMS webhooks
- Support future phone-call workflows if voice is added later

---

### 8. Email Provider (SendGrid, Resend, or Postmark)
Outbound and possibly inbound email handling.

**Responsibilities**
- Send email replies
- Support inbound lead email handling if configured

---

### 9. Google Calendar or Microsoft 365 Calendar
Scheduling integration layer.

**Responsibilities**
- Check available appointment times
- Create consultation events
- Prevent overlapping bookings
- Support reschedule and cancellation workflows

---

### 10. Phoenix or LangSmith
Tracing and observability layer for AI workflows.

**Responsibilities**
- Trace model calls
- Inspect retrieval quality
- Track failures and latency
- Debug bad outputs or missing context

---

### 11. Ragas
Evaluation framework for measuring RAG quality.

**Responsibilities**
- Evaluate answer groundedness
- Evaluate retrieval relevance
- Evaluate consistency and fallback behavior
- Help prevent quality regression over time

---

## High-Level Data Flow

### A. Lead Intake
A lead enters the system through one of these channels:
- website form
- SMS
- email

The backend receives the inbound event and stores the raw message.

---

### B. Normalization
The backend converts the inbound event into a standard internal format.

Example:
- source channel
- sender name
- sender contact
- message body
- timestamp
- agency ID
- conversation ID

This step is important because SMS, form submissions, and email all arrive in different shapes.

---

### C. Intent + Intake Analysis
The backend sends the normalized message to the AI layer to classify the message.

Typical outputs:
- service inquiry
- scheduling request
- reschedule request
- general question
- out-of-scope question
- escalation needed

The AI should return a **structured result**, not just a paragraph of text.

---

### D. Retrieval (RAG)
If the lead asks a question about services, policies, availability, or agency-specific rules, the backend runs retrieval against approved agency documents.

The retrieval step should only search trusted sources such as:
- agency services list
- approved FAQ documents
- scheduling rules
- intake rules
- coverage/service area notes
- approved response templates

The system must not answer from unapproved or unknown sources.

---

### E. Response Planning
The backend combines:
- the lead message
- retrieved context
- business rules
- channel type
- current conversation state

It then asks the AI layer to produce a structured reply plan.

This reply plan should answer:
- can the system reply safely?
- what information is missing?
- should follow-up questions be asked?
- should scheduling be offered?
- should this be escalated to staff?

---

### F. Response Rendering
The final user-facing response is built from the structured reply plan.

This allows:
- different formatting for SMS vs email
- consistent brand voice
- safe fallback messages
- less random behavior from the model

---

### G. Scheduling
If the lead is ready to book a consultation:
- the backend checks available times from the calendar integration
- offers valid time slots
- books the selected slot
- stores the appointment in the database
- updates lead status
- triggers reminder workflows if configured

If a lead needs to reschedule, the same scheduling service handles that flow.

---

### H. Summary Generation
When enough intake information has been collected or a consultation is booked, the system creates a summary for staff.

Typical summary fields:
- lead name
- requested service
- location
- important needs mentioned
- questions asked
- scheduled time
- unresolved concerns
- escalation reasons if any

---

### I. Dashboard + Staff Review
Staff members use the dashboard to:
- review lead details
- review conversation history
- see summaries
- see scheduled calls
- handle escalations
- correct issues when automation fails

---

### J. Logging and Audit Trail
The system logs important events such as:
- inbound message received
- AI classification result
- retrieval success or failure
- response sent
- appointment booked
- escalation triggered
- external service failure

These logs are needed for debugging, monitoring, and compliance review.

---

## External Dependencies

### Required
- OpenAI for model inference
- Twilio for SMS
- Postgres / Supabase for data storage
- Google Calendar or Microsoft 365 for scheduling

### Optional / Recommended
- SendGrid, Resend, or Postmark for email
- Phoenix or LangSmith for tracing
- Ragas for evals

---

## Failure Points

### 1. Missing or weak retrieval context
The system may not find enough trusted information to answer a question safely.

**Expected behavior**
- do not guess
- return a safe fallback
- escalate to a human if needed

---

### 2. Bad structured output
The model may return data in the wrong schema or omit required fields.

**Expected behavior**
- validate model output
- reject invalid output
- retry once if safe
- escalate or use fallback if still invalid

---

### 3. Hallucinated answer
The model may generate text that is not supported by approved context.

**Expected behavior**
- require retrieval for agency-specific claims
- use evals to detect drift
- block unsupported answers when confidence is low

---

### 4. Channel formatting mismatch
SMS, email, and form replies may require different formatting.

**Expected behavior**
- keep rendering logic separate by channel
- do not let one shared template handle every case blindly

---

### 5. Calendar integration failure
The scheduling provider may be unavailable or return inconsistent availability.

**Expected behavior**
- do not confirm bookings without provider confirmation
- show fallback message
- notify staff of manual scheduling need

---

### 6. Twilio or email provider outage
Outbound or inbound communication may fail.

**Expected behavior**
- log the failure
- retry if appropriate
- flag the lead for human follow-up

---

### 7. Database or API failure
The backend, DB, or external API may fail during processing.

**Expected behavior**
- fail safely
- do not lose lead state silently
- log the failure with enough detail to investigate
- support retries for recoverable actions

---

### 8. Duplicate event processing
A webhook may be delivered more than once.

**Expected behavior**
- use idempotency keys or event deduplication
- prevent duplicate messages or duplicate bookings

---

### 9. Sensitive data appears unexpectedly
Even if the system is designed to avoid PHI, users may still type private information into messages.

**Expected behavior**
- minimize storage where possible
- avoid unnecessary logging of raw sensitive text
- document data handling rules clearly

---

### 10. Vendor quota / rate limit / billing failure
Model usage, SMS volume, or email limits may be hit.

**Expected behavior**
- monitor quotas
- alert staff
- degrade gracefully instead of silently failing

---

## Human Handoff Points

A real person should take over when:

- the system does not have enough trusted information to answer safely
- the lead asks a medical or clinical question
- the lead asks something outside approved services or policy
- scheduling fails
- the lead is upset, confused, or asks repeatedly for a human
- the system detects low confidence or conflicting context
- external services are down
- the lead is high-priority and agency rules require staff handling
- the conversation reaches the point where a real consultation must happen

---

## Safe Failure Rule

If the system cannot answer using trustworthy approved context, it must say some version of:

> “I don’t have enough reliable information to answer that right now, but I can connect you with a team member.”

This is a product rule, not just a prompt suggestion.

---

## Out of Scope for MVP

The first version should not include:
- medical diagnosis
- treatment recommendations
- insurance determination
- autonomous voice call handling
- fully autonomous case intake without staff review
- complex multi-step care coordination

Voice may be added later, but it should not block MVP delivery.

---

## Recommended MVP Architecture Summary

For the first 30-day version:

- Next.js dashboard
- FastAPI backend
- Postgres / Supabase
- pgvector
- LlamaIndex
- OpenAI Responses API
- Twilio for SMS
- Google Calendar or Microsoft 365 Calendar
- Phoenix or LangSmith
- Ragas

This version should focus on:
- inbound lead capture
- question answering from approved sources
- structured intake follow-up
- scheduling
- summaries
- dashboard visibility
- logging and escalation