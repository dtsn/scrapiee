#!/usr/bin/env python3
"""
Quick test runner for Scrapiee test suite
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tests.test_suite import main

if __name__ == "__main__":
    print("🚀 Running Scrapiee Test Suite...")
    asyncio.run(main())