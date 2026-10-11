"""
Learning Path Generator - Subdirectory Entry Point
Delegates execution cleanly to dashboard.main().
"""

import sys
import os

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from dashboard import main

if __name__ == "__main__":
    main()
