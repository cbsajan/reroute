"""
Pytest Configuration for REROUTE Tests

Ensures proper import paths for the reroute package during testing.
"""

import sys
from pathlib import Path

# Add the parent directory to sys.path to ensure proper imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
