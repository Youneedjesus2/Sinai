# Glossary
Healthcare AI Lead Intake Agent

---

## Agent
A software system that can take input, reason about what to do, and perform actions such as replying, asking follow-up questions, or scheduling a call.

In this project, the agent does not act freely. It must follow business rules and approved workflows.

---

## Approved Source
A trusted source of information the system is allowed to use when answering questions.

Examples:
- agency website pages
- approved FAQ content
- approved service documents
- approved scheduling rules

The system should not answer from unknown or unreviewed sources.

---

## Audit Log
A record of important system events.

Examples:
- inbound message received
- response sent
- escalation triggered
- appointment booked
- retrieval failed

Audit logs help with debugging and review.

---

## Channel
The way a lead communicates with the system.

Examples:
- SMS
- email
- website form

Different channels may require different formatting rules.

---

## Chunk
A small piece of a document stored for retrieval.

Long documents are split into chunks so the retrieval system can search them more effectively.

---

## Confidence
A signal used by the system to decide how safe it is to continue automatically.

Low confidence should lead to a fallback response or human escalation.

---

## Escalation
The act of handing the conversation to a real human.

This happens when the system cannot answer safely, the lead asks for a human, or a workflow fails.

---

## Embedding
A numerical representation of text used for semantic search.

Embeddings help the system find text with similar meaning, even if the words are not exactly the same.

---

## Eval
A test used to measure AI system quality.

Examples:
- groundedness
- retrieval relevance
- scheduling success
- escalation correctness

---

## Grounded Response
A response that is supported by approved context rather than invented by the model.

---

## Hallucination
When the model produces information that is false, unsupported, or not present in approved sources.

---

## Human Handoff
A transition from automated handling to staff handling.

---

## Intake
The early stage of collecting information from a lead.

Examples:
- what service is needed
- where care is needed
- preferred schedule
- whether the person wants a consultation

---

## Lead
A potential client or family member contacting the agency to ask about services.

---

## LLM
Large Language Model.

This is the AI model used to interpret messages, produce structured outputs, and generate replies.

---

## Orchestrator
The backend logic that controls the workflow.

It decides:
- whether retrieval is needed
- whether a reply can be sent
- whether scheduling should happen
- whether escalation is required

---

## Prompt
The instructions given to the model.

Prompts help control tone, format, restrictions, and workflow behavior.

---

## RAG
Retrieval-Augmented Generation.

This means the system first finds relevant approved information, then uses that information to generate a response.

In plain English:
the AI looks things up before answering.

---

## Retrieval
The step where the system searches approved knowledge sources for relevant information.

---

## Structured Output
A model response in a fixed format such as JSON instead of free-form text.

Structured outputs make the system easier to validate and safer to automate.

---

## Tool Call
When the model asks the system to perform an action such as checking calendar availability or booking a consultation.

Tool calls should always be validated by backend rules before execution.

---

## Vector Search
A search method that compares embeddings to find text with similar meaning.

---

## Webhook
An automated HTTP request sent from one service to another when an event happens.

Examples:
- inbound SMS from Twilio
- email delivery event
- scheduling event callback