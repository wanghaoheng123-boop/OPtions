# Agent Routing and Governance

## Canonical Roles
| Role | Scope | Required Output |
|------|-------|-----------------|
| Orchestrator | sequencing, prioritization, final merge gate | plan + decisions + final verification matrix |
| ResearchAgent | references, external validation, docs lookup | dense evidence summary + citations |
| CodeAgent | implementation in assigned modules | changed files + rationale + tests run |
| AdversarialReviewer | contrarian review and risk discovery | prioritized findings + severity + remediation |
| Supervisor | release readiness sign-off | go/no-go with residual risks |

## Dispatch Rules
1. Route by domain and directory ownership.
2. Delegate complex work; require concise returns.
3. Never mark complete without explicit validation evidence.
4. Log handoff state in `activeContext.md` before and after delegation.

## Required Review Checklist
- Data source provenance verified.
- API/UI contracts validated.
- Failure paths handled and surfaced.
- Security/secrets policy respected.
- Regression or targeted tests executed.
- Residual risk documented.

## Validation Tiers
- Quick: `<fast_test_commands>`
- PR-ready: `<quick + integration/e2e>`
- Release: `<full_validation_matrix>`

## Tooling Notes
- Preferred shell and package manager: `<notes>`
- Cross-platform caveats: `<notes>`
