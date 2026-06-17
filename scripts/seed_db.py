#!/usr/bin/env python3
"""Thin wrapper — canonical seed lives in backend/scripts/seed_db.py."""

import runpy
import sys
from pathlib import Path

_BACKEND_SEED = Path(__file__).resolve().parent.parent / "backend" / "scripts" / "seed_db.py"

if __name__ == "__main__":
    sys.path.insert(0, str(_BACKEND_SEED.parent.parent))
    runpy.run_path(str(_BACKEND_SEED), run_name="__main__")
