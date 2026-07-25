# ADR-0005: Test pyramid and requirement traceability

- Status: Accepted
- Requirements: REQ-TEST-001..008

## Decision

Optimise for many standalone unit/component tests and few integration/acceptance tests.
Every behavioural test references a valid requirement marker. CI validates unknown and
orphan IDs, while release evidence maps requirements to code, tests and release scope.

Something is considered implemented only when it has passed an automated unit,
component or integration test at the lowest appropriate level. UAT is excluded from
this implementation criterion: it verifies representative user workflows, acceptance
criteria and fitness for intended use, but does not repeat or replace verification from
lower levels. A defect first observed during UAT receives a lower-level reproducing
test before its fix is complete.

## Consequences

Scientific algorithms stay independent of UI and filesystem concerns. Planning and test
metadata carry modest maintenance cost in exchange for auditable change impact. UAT
remains small and interpretable instead of becoming a slow second implementation test
suite.
