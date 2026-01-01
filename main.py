from __future__ import annotations

import sys
from pathlib import Path


# Ensure src/ is on sys.path for local execution without installation
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nmgui import main  # type: ignore  # added after sys.path adjustment


if __name__ == "__main__":
    main()
