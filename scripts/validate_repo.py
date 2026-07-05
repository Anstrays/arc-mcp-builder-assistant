#!/usr/bin/env python3
"""Run the canonical Arc Builder Kit repository validator."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from arc_builder_kit.validate_repo import main  # noqa: E402


if __name__ == "__main__":
    main()
