"""
MedResearch AI — Entry point for the eval harness.

Usage:
    python run_evals.py
"""

import asyncio
from evals.harness import run_all


if __name__ == "__main__":
    asyncio.run(run_all())