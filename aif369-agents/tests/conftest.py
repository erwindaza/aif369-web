"""Pytest configuration"""
import sys
import os
from pathlib import Path

# Add parent directory to path so local imports work
parent_dir = Path(__file__).parent.parent
parent_str = str(parent_dir.absolute())
if parent_str not in sys.path:
    sys.path.insert(0, parent_str)

# Also change working directory to parent
os.chdir(parent_dir)
