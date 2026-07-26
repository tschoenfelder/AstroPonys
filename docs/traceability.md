# Traceability matrix

This matrix is intentionally compact at project foundation. Before implementation,
Sprint 1 ranges are expanded to individual code modules and test node IDs by AP-001.
Detailed Sprint 1 acceptance IDs are defined in `docs/sprints/sprint-1.md`.

| Requirement group | Decision | Task | Planned verification | Release |
|---|---|---|---|---|
| REQ-CFG-001..006 | ADR-0001 | AP-002 | unit + component | v0.1.0 |
| REQ-FITS-001..007 | ADR-0001, ADR-0002 | AP-003 | unit + component | v0.1.0 |
| REQ-STORAGE-001..004 | ADR-0002 | AP-003 | component hashes | v0.1.0 |
| REQ-FOCUS-001..006 | ADR-0003 | AP-004 | unit + synthetic component | v0.1.0 |
| REQ-FOCUS-007..011 | ADR-0003, ADR-0004 | AP-005, AP-008 | unit + golden + private optional | v0.1.0 |
| REQ-CONTACT-001..006 | ADR-0001 | AP-006 | component + visual golden | v0.1.0 |
| REQ-CLI-001..005 | ADR-0001 | AP-007 | integration | v0.1.0 |
| REQ-SAFETY-001..004 | ADR-0002 | AP-001, AP-007 | unit + integration | v0.1.0 |
| REQ-TEST-001..008 | ADR-0005 | AP-001, AP-008, AP-009 | meta-tests + CI + release audit | v0.1.0 |
| REQ-PLATFORM-001..004 | ADR-0006 | AP-001 | Windows 3.13 gate + wheel install audit | v0.1.0 |
| REQ-SCI-001..006 | ADR-0004 | AP-001, AP-004..006, AP-009 | unit + release audit | v0.1.0 |
| REQ-AUTOFOCUS-001..008 | ADR-0007, METHOD-AUTOFOCUS-001 | AP-010 | synthetic unit + private compatibility | v0.1.0 |
