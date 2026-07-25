# ADR-0006: Primary platform and binary dependency policy

- Status: Accepted
- Requirements: REQ-PLATFORM-001..004

## Context

The Windows workstation is faster than the Raspberry Pi and will be the primary
runtime for analysis. The current local interpreter is Python 3.13. Scientific Python
packages may lag new interpreter releases or require difficult local compilation,
especially on Windows.

## Decision

Use Windows with Python 3.13 as the primary development and release-validation
environment. Keep Python 3.11+ compatibility where practical, but prioritise a stable
interpreter/dependency combination over adopting each newest Python release.

Select required libraries only after confirming maintained precompiled Windows wheels
for the chosen Python versions. Local compilation on Windows is not a normal
installation path. Exceptions require an ADR with justification and installation and
maintenance consequences.

Linux and Raspberry Pi/ARM64 remain supported secondary platforms. Platform-specific
optimisation and native Raspberry Pi release gates may follow after the desktop MVP.

## Consequences

Windows installation remains predictable and avoids compiler toolchain requirements.
Some package upgrades or future Python versions may be intentionally delayed. CI and
release evidence must distinguish the primary Windows/Python 3.13 gate from secondary
compatibility checks.
