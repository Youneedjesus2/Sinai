# Reviewer Checklist

## Correctness
- [ ] Business logic matches the issue
- [ ] Structured outputs are validated
- [ ] Channel-specific formatting is correct

## RAG quality
- [ ] Answers rely on approved sources
- [ ] Unsafe guessing is blocked
- [ ] Missing-context fallback exists
- [ ] Citations/provenance available when needed

## Safety
- [ ] Escalation rules are enforced
- [ ] Emergency / high-risk language is handled safely
- [ ] No forbidden claims are introduced

## Scheduling
- [ ] No overlap risk introduced
- [ ] Failure path exists if calendar API fails
- [ ] Reschedule/cancel logic is safe

## Security / privacy
- [ ] Sensitive data minimized
- [ ] Secrets not exposed
- [ ] Logs do not leak unnecessary user data
- [ ] Retention behavior documented

## Observability
- [ ] Errors logged with context
- [ ] Audit events added where needed
- [ ] Metrics/traces support debugging

## Release readiness
- [ ] Tests passed
- [ ] Evals passed
- [ ] Rollback plan is clear