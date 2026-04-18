# Active context (volatile — last session handoff)

## Current focus

Browser QA (Playwright), optimization-loop baselines, external OSS and literature survey captured in [`findings.md`](findings.md); research backlog items ready to become GitHub Issues.

## Last actions

- Added Playwright config and E2E specs under [`frontend/e2e/`](frontend/e2e/) with API route mocks; `aria-label` on search button; `data-testid` on app shell and error banner.
- Extended CI with a **`playwright`** job (Node 20, `npm ci`, `playwright install --with-deps chromium`, `npm run test:e2e`).
- Documented optimization metrics, OSS landscape, DOI-based paper shortlist, and prioritized research backlog in [`findings.md`](findings.md).
- Added [`scripts/baseline_metrics.py`](scripts/baseline_metrics.py) and README §6b.

## Immediate next steps

1. Create GitHub Issues from the **Research backlog** list in `findings.md` (labels `research` / `quant` / `ui`).
2. If `VITE_API_URL` is used in deploy, confirm it is **origin-only** (no trailing `/api`).
3. Human reviewers: extend E2E mocks for `/api/statarb` and `/api/heatmap` if Vite proxy noise in logs becomes a failure signal.

## Adversarial batch sign-off (this deliverable)

Documentation, automation, and honest scoping (no profit guarantees) reviewed against [`AGENTS.md`](AGENTS.md) checklist: **pass** for merged artifacts.

**Supervisor:** approve when Playwright job is green on `main` and research Issues are triaged.
