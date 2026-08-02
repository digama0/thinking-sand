#!/usr/bin/env python3
"""check-all — run every layer scoreboard, L7 down to L0 (the book's reading order).

Exit code is nonzero iff any layer reported a FAIL. Pass --list to print the
obligation census without running anything.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORDER = [7, 6, 5, 4, 3, 2, 1, 0]

rc = 0
for n in ORDER:
    r = subprocess.run([sys.executable, str(HERE / f"check-l{n}.py"), *sys.argv[1:]])
    rc |= r.returncode
    print()
sys.exit(rc)
