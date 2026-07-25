# ADR-0001: Session configuration and output layout

- Status: Accepted
- Requirements: REQ-CFG-001..006, REQ-CONTACT-006, REQ-CLI-001..005

## Decision

Use one versioned `astroponys.yaml` beside the session images. Load it by explicit
path or adjacency only. Write immutable pony runs below
`astroponys-output/<pony>/<run-id>/`.

## Consequences

Sessions are portable and avoid contradictory configuration. Tools share provenance
and output conventions. Users must select a session rather than rely on global search.
