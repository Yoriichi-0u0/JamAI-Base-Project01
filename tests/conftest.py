"""
Pytest configuration to ensure the repository root is on sys.path.

This lets tests import the local `app` package without requiring installation.
"""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

