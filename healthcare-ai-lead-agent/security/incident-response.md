# Incident Response Policy
Healthcare AI Lead Intake Agent

---

# 1. Purpose

This document defines how security, privacy, and major operational incidents are identified, handled, documented, and reviewed.

An incident is any event that may cause:
- unauthorized data exposure
- unsafe automated behavior
- service disruption
- abuse of external integrations
- loss of trust in system outputs

---

# 2. Incident Types

Examples of incidents include:

- suspected data exposure
- leaked API key
- unauthorized dashboard access
- prompt injection causing unsafe behavior
- malicious document ingestion
- repeated hallucinated answers sent to leads
- mass scheduling abuse
- vendor compromise or outage with serious user impact

---

# 3. Incident Severity

## Severity 1 — Critical
Major data exposure, credential leak, or widespread unsafe behavior.

Examples:
- exposed production database
- leaked OpenAI or Twilio production credentials
- system sending unsafe messages broadly

## Severity 2 — High
Serious system failure or contained security issue.

Examples:
- unauthorized access to one tenant
- repeated calendar abuse
- failure in escalation for high-risk messages

## Severity 3 — Moderate
Limited impact incident with available workaround.

Examples:
- isolated logging failure
- temporary webhook replay issue
- one broken reply template

## Severity 4 — Low
Minor issue with little or no user harm.

Examples:
- non-sensitive alert noise
- harmless formatting bug

---

# 4. Response Goals

When an incident happens, the team should:

1. contain the problem
2. protect users and agency data
3. restore safe operation
4. document what happened
5. prevent repeat incidents

---

# 5. Detection Sources

Incidents may be detected through:

- monitoring alerts
- failed evals
- staff reports
- user complaints
- vendor alerts
- unusual logs or audit events

---

# 6. Initial Response Steps

When an incident is suspected:

1. create an incident record
2. assign severity
3. identify affected systems
4. contain the issue if possible
5. notify internal stakeholders
6. begin evidence collection

Examples of containment:
- disable outbound messaging
- disable scheduling actions
- revoke compromised API keys
- pause document ingestion
- force manual human handling only

---

# 7. Containment Actions

Depending on the incident, containment may include:

- rotating credentials
- disabling a vendor integration
- pausing AI replies
- pausing booking actions
- disabling specific prompts or workflows
- restricting dashboard access

Containment should prioritize safety over automation continuity.

---

# 8. Recovery

After containment:

1. confirm root cause
2. apply technical fix
3. test in a controlled environment
4. restore service gradually
5. monitor closely for recurrence

---

# 9. Communication

Communication should be clear and factual.

Internal updates should include:
- what happened
- what systems are affected
- what is disabled
- what actions are in progress
- what risks remain

Do not speculate without evidence.

---

# 10. Evidence Collection

Preserve:
- logs
- audit events
- request IDs
- vendor incident details
- deployment history
- changed prompts or configs
- affected message or lead IDs

Avoid changing or deleting evidence before review.

---

# 11. Post-Incident Review

Every significant incident should produce a short review covering:

- timeline
- impact
- root cause
- containment steps
- fix applied
- follow-up tasks
- whether docs, tests, or evals need updates

---

# 12. Required Follow-Up

After an incident, consider whether to update:

- threat-model.md
- data-governance.md
- runbooks.md
- eval datasets
- prompts
- release rules

---

# 13. Example Immediate Actions by Incident

## Credential Leak
- revoke key
- rotate key
- inspect usage logs
- redeploy with new secret

## Unsafe AI Reply Pattern
- disable affected prompt path
- route to human-only handling
- inspect traces and retrieval behavior

## Vendor Outage
- pause affected workflow
- enable fallback messaging
- flag leads for manual follow-up

## Unauthorized Access
- revoke session or credentials
- inspect access logs
- restrict affected accounts