"""Pytest fixtures: load FastAPI app from backend/main.py (repo root on path)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def api_client():
    sys.path.insert(0, str(ROOT))
    backend_dir = ROOT / "backend"
    main_path = backend_dir / "main.py"
    spec = importlib.util.spec_from_file_location("terminal_main", main_path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    from fastapi.testclient import TestClient

    return TestClient(mod.app)
