#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CDO AI Modules - Main Entry Point
Production-ready intent analysis system with modular architecture
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from cdo_ai.cli.main import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Application failed to start: {e}")
        sys.exit(1)
