#!/usr/bin/env python3
"""
Integration Test Runner for Scrapiee
Runs the complete integration test suite against local FastAPI server
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tests.test_integration import main

if __name__ == "__main__":
    print("🚀 Running Scrapiee Integration Tests...")
    asyncio.run(main())