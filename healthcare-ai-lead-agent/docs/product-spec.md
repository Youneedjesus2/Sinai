# Product Specification
Healthcare AI Lead Intake Agent

---

# 1. Overview

This system helps healthcare agencies respond to inbound leads automatically, collect intake information, answer service-related questions using approved agency knowledge, and schedule consultation calls with staff.

The goal is to reduce manual lead handling work while ensuring responses remain accurate, consistent, and safe.

The AI assistant acts as a **lead intake proxy**, not a clinical advisor. It assists with communication, scheduling, and summarization before a human consultation.

---

# 2. Problem Statement

Healthcare agencies often receive inbound inquiries through:

- website forms
- SMS messages
- emails
- phone calls

Staff members must manually:

- respond to questions
- ask intake questions
- determine service fit
- schedule consultations
- summarize conversations

This process is time-consuming and inconsistent.

Many leads also arrive outside business hours and may never receive timely responses.

The system aims to automate the early stages of this workflow.

---

# 3. Product Goals

The system should:

1. Respond to inbound leads quickly and consistently.
2. Answer common service-related questions using approved agency information.
3. Ask follow-up intake questions to understand the lead's needs.
4. Offer and schedule consultation calls with agency staff.
5. Generate summaries of conversations for staff review.
6. Escalate conversations to humans when automation is unsafe or insufficient.
7. Provide a dashboard for staff to track leads and appointments.

---

# 4. Non-Goals

The system must NOT:

- Provide medical diagnosis
- Provide treatment recommendations
- Interpret symptoms clinically
- Guarantee service availability or insurance coverage
- Replace human consultation
- Store unnecessary sensitive patient data
- Make decisions about care eligibility

The system is designed to support **lead intake and scheduling only**.

---

# 5. User Personas

## Persona 1: Healthcare Agency Intake Coordinator

**Description**

An employee responsible for responding to new inquiries and scheduling consultations.

**Needs**

- Quickly see new leads
- Read conversation history
- View AI summaries
- Confirm or adjust scheduled consultations
- Intervene when automation fails

**Pain Points**

- High message volume
- Repetitive intake questions
- Time spent scheduling calls
- Leads contacting outside business hours

---

## Persona 2: Potential Client (Lead)

**Description**

A person contacting the agency to ask about services for themselves or a family member.

**Needs**

- Quick response
- Clear explanation of services
- Easy scheduling process
- Ability to speak with a human if needed

**Pain Points**

- Uncertainty about services offered
- Waiting for responses
- Difficulty scheduling consultations

---

## Persona 3: Agency Owner / Administrator

**Description**

Person responsible for operations and lead conversion.

**Needs**

- Visibility into lead activity
- Reduced staff workload
- Consistent responses to potential clients
- Increased consultation bookings

---

# 6. Core Workflows

## Workflow 1 — New Lead Inquiry

1. A lead sends a message through:
   - website form
   - SMS
   - email

2. The system receives the message and stores it.

3. The system analyzes the message to determine intent.

4. If the message asks about services:
   - the system retrieves approved agency information
   - generates a safe response

5. The system sends a reply asking follow-up intake questions if needed.

6. The conversation continues until:
   - enough information is collected, or
   - scheduling is offered.

---

## Workflow 2 — Question Answering

1. A lead asks a question about services.

2. The system retrieves relevant approved documents.

3. The AI generates a response using that context.

4. If trusted context is missing:
   - the system provides a safe fallback response
   - or escalates to a human.

---

## Workflow 3 — Consultation Scheduling

1. The system determines that the lead is ready to schedule a consultation.

2. The system checks calendar availability.

3. The system offers available time slots.

4. The lead selects a time.

5. The system creates a calendar event.

6. The system confirms the appointment.

7. The system stores the appointment in the database.

---

## Workflow 4 — Conversation Summary

After intake questions are answered or a consultation is scheduled:

1. The system generates a structured summary.

Summary may include:

- lead name
- requested services
- location
- care needs described
- important concerns mentioned
- consultation time
- unresolved questions

2. The summary becomes visible in the staff dashboard.

---

## Workflow 5 — Escalation to Human

The system escalates to staff when:

- the lead asks a clinical question
- the system lacks trusted information
- scheduling fails
- the lead requests a human
- the conversation becomes confusing
- the lead expresses frustration

Staff can then take over communication.

---

# 7. Acceptance Criteria

The system is considered working when the following conditions are met.

---

## Lead Intake

- System receives inbound messages from form, SMS, or email.
- Messages are stored with sender information and timestamps.
- Conversations are linked to a lead record.

---

## Question Answering

- Responses reference only approved agency sources.
- If trusted information is missing, the system provides a safe fallback.
- The system does not generate medical advice.

---

## Intake Follow-Up

- The system can ask follow-up questions to clarify needs.
- Conversation context persists across messages.

---

## Scheduling

- The system can retrieve available time slots from a calendar provider.
- The system prevents overlapping bookings.
- Appointments are stored in the database.
- Confirmation messages are sent after booking.

---

## Dashboard

Staff can:

- view lead records
- view conversation history
- view summaries
- see scheduled consultations
- identify escalated conversations

---

## Summaries

After intake or scheduling:

- the system generates a readable summary
- the summary includes relevant intake information

---

## Escalation

The system must escalate when:

- the system cannot answer safely
- a lead asks clinical questions
- the system detects low confidence
- scheduling fails

---

# 8. Success Metrics

Early success may be measured by:

- response time to inbound leads
- percentage of leads receiving automated responses
- number of consultations scheduled
- number of escalations required
- reduction in manual intake workload

---

# 9. Out of Scope for MVP

The first version will NOT include:

- AI phone call handling
- insurance verification
- clinical triage
- advanced patient intake forms
- complex CRM integrations
- automated care plan generation

These may be considered in future versions.

---

# 10. Future Expansion

Potential future capabilities:

- AI phone call assistant
- multi-agency SaaS platform
- advanced lead analytics
- insurance pre-qualification
- automated follow-up reminders
- multilingual support
- CRM integrations
- System must respond within 5 seconds
- System must support 500 leads per day
- System must support multiple agencies
- System must store message history for 30 days