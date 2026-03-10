# Changelog

## Unreleased

### Added
- Built a minimal FastAPI backend happy-path for inbound lead intake with route, service, repository, and schema separation.
- Added normalized data models and persistence for leads, conversations, messages, appointments, summaries, and audit events.
- Implemented a rule-based orchestrator v1 that returns validated structured next-action output.
- Added audit logging for lead creation, conversation creation, inbound message receipt, orchestration completion, and outbound reply creation.
- Added initial SQL migration for core tables and basic unit/integration tests for orchestrator and end-to-end intake flow.
