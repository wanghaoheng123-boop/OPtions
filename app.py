"""Vercel FastAPI entry — re-export backend app so the full repo is bundled."""

from backend.main import app

__all__ = ["app"]
