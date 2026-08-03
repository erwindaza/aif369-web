"""Pytest configuration"""
import sys
import os
from pathlib import Path

# Ensure we're using absolute paths
tests_dir = Path(__file__).parent.absolute()
parent_dir = tests_dir.parent.absolute()
aif369_agents_dir = parent_dir

# Add to sys.path FIRST, before any imports
if str(aif369_agents_dir) not in sys.path:
    sys.path.insert(0, str(aif369_agents_dir))

# Change working directory to aif369-agents
os.chdir(aif369_agents_dir)
