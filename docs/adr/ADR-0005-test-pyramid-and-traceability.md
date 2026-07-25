# ADR-0005: Test pyramid and requirement traceability

- Status: Accepted
- Requirements: REQ-TEST-001..004

## Decision

Optimise for many standalone unit/component tests and few integration/acceptance tests.
Every behavioural test references a valid requirement marker. CI validates unknown and
orphan IDs, while release evidence maps requirements to code, tests and release scope.

## Consequences

Scientific algorithms stay independent of UI and filesystem concerns. Planning and test
metadata carry modest maintenance cost in exchange for auditable change impact.
