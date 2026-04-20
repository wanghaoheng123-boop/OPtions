# Cross-Platform Synchronization Runbook

## Scope

This runbook governs handoff and continuity across:

- Cursor, Claude Code, Antigravity
- MacBook, Mac Mini, Windows PC
- Shared synchronized filesystem (e.g., Google Drive)

## Startup Checklist (Any Device)

1. Confirm synchronized root is fully up to date.
2. Open and read in order:
   - `AGENTS.md`
   - `activeContext.md`
   - latest entry in `progress.md`
3. Confirm repo state:
   - current branch,
   - unstaged/staged changes,
   - pending local artifacts.
4. Run minimal smoke checks before edits:
   - fast local test command(s),
   - one contract sanity check command if applicable.

## Pre-Switch Handoff Protocol

Before leaving a device/tool session:

1. Update `activeContext.md`:
   - current objective,
   - last completed action,
   - immediate next action,
   - blockers and assumptions.
2. Append a checkpoint in `progress.md` with:
   - commands run,
   - outcomes,
   - unresolved risks.
3. Ensure all critical files are flushed to synchronized storage.
4. Avoid leaving ambiguous partial edits without notes.

## Post-Switch Resume Protocol

On the next device/tool:

1. Pull latest synchronized state.
2. Re-read `activeContext.md` and latest `progress.md` checkpoint.
3. Rebuild context quickly:
   - what was done,
   - what is next,
   - what is blocked.
4. Run quick smoke checks to validate environment parity.
5. Continue with the next explicit step only.

## File Lock and Conflict Policy

When concurrent edits conflict:

1. Treat `activeContext.md` as authoritative for immediate intent.
2. Merge `progress.md` append-only entries; never delete history.
3. Resolve semantic conflicts in governance docs (`AGENTS.md`) manually.
4. Record conflict resolution outcome in `progress.md`.

## Environment Parity Matrix

Track and compare:

- OS and shell (`pwsh`, `bash`, `zsh`)
- language runtime versions
- package manager versions
- critical env vars and secret availability

If parity mismatch affects execution, document mitigation before proceeding.

## Minimal Validation Commands Before Resuming

Use project-specific equivalents, but keep this structure:

1. Fast tests (unit/smoke)
2. Lint/type checks (if configured)
3. One workflow-level validation (API smoke or E2E smoke)

Do not run full release validation unless scope requires it.
