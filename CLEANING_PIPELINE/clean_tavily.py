#!/usr/bin/env python
"""
Convenience script for running the Tavily Cleaner CLI.
"""

import sys
import os

# Add the project root to the path so we can import from CLEANING_PIPELINE
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from CLEANING_PIPELINE.tavily_cleaner.cli import main

if __name__ == "__main__":
    main()
