# Tech context

## Stack

- Python 3.10+, FastAPI, pandas, numpy, scipy, sklearn, hmmlearn, yfinance, httpx.
- Node 20+, Vite 8, React 19, lightweight-charts 5, Tailwind 4, axios.

## Environments

- **Local**: `uvicorn backend.main:app --port 8005`; Vite dev proxies `/api` → 8005 ([`frontend/vite.config.ts`](frontend/vite.config.ts)).
- **Vercel**: build frontend + Python function; no Vite proxy—browser calls same-origin `/api`.

## Google Drive / multi-machine

If the repo is synced via Drive/iCloud:

- Use **git** as source of truth; avoid two machines editing the same file unsynced.
- Prefer **branches + push** over conflict-prone “shared folder live edit.”

## Formatting

- Python: match existing modules; type hints where new code is added.
- TSX: keep `@ts-nocheck` only where legacy; new components prefer typed props.

## Windows vs macOS

- **Symlink**: `CLAUDE.md` may be a small pointer file instead of `ln -s` if Developer Mode symlink is unavailable.
