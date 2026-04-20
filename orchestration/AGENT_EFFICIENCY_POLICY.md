# Agent Efficiency Policy

## Objective

Maximize outcome quality per token/minute by:

- routing work to the right agent lane,
- minimizing redundant full-context passes,
- applying tiered validation proportional to scope.

## Lane Model

Use parallel lanes when scope spans domains:

1. Research lane: references, prior art, claim validation.
2. Implementation lane(s): backend/frontend/core code.
3. Review lane: adversarial validation and contract checks.

Single-lane mode is acceptable for small isolated tasks.

## Delegation Contract

Each sub-agent must return only:

- concise findings,
- changed file paths,
- commands/tests run,
- unresolved risks.

Reject verbose raw logs unless explicitly requested.

## Validation Tiers

### Tier Quick
Run on every meaningful edit cycle:

- fast tests/smoke checks,
- narrow scope checks tied to changed files.

### Tier PR-Ready
Run before integration:

- quick tier +
- integration/E2E relevant to changed area.

### Tier Release
Run only for release/hardening scope:

- full backend tests,
- regression scripts,
- batch/institutional gates,
- frontend E2E.

## Anti-Redundancy Rules

1. Do not rerun full release gates after docs-only edits.
2. Do not run network-heavy checks if unchanged scope is offline-only.
3. Reuse prior green evidence when commit hash and relevant files are unchanged.
4. Trigger heavy reruns only when risk class changes (data/contract/logic/security).

## KPI Set

Track per task/PR:

- cycle time (start to validated completion),
- number of validation reruns,
- failures caught pre-merge vs post-merge,
- reopen rate due to missed issues,
- average sub-agent count and parallelization ratio.

## Escalation Policy

Escalate to adversarial review when:

- architecture changes,
- strategy/math changes,
- security-sensitive behavior changes,
- repeated regressions occur.

## Reporting Standard

Every completion report must include:

1. what changed,
2. what was verified,
3. what remains risky,
4. what should happen next.
