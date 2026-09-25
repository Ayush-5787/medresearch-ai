"""
MedResearch AI — Base Agent
Shared behavior for all agents: logging, timing, trace recording.
"""

import time
from abc import ABC, abstractmethod
from typing import List
from core.schemas import AgentStep
from core.llm import get_llm


class BaseAgent(ABC):
    """Abstract base class for all MedResearch agents."""

    def __init__(self, name: str):
        self.name = name
        self.llm = get_llm()
        self.trace: List[AgentStep] = []

    def log_step(
        self,
        action: str,
        input_summary: str,
        output_summary: str,
        duration_ms: int = 0,
    ) -> AgentStep:
        """Record an action in the trace."""
        step = AgentStep(
            agent_name=self.name,
            action=action,
            input_summary=input_summary[:500],
            output_summary=output_summary[:500],
            duration_ms=duration_ms,
        )
        self.trace.append(step)
        print(f"[{self.name}] {action} | {input_summary[:60]}... → {output_summary[:60]}...")
        return step

    def clear_trace(self):
        """Reset the trace before a new run."""
        self.trace = []

    @abstractmethod
    async def run(self, *args, **kwargs):
        """Each agent implements its own run method."""
        pass


class Timer:
    """Context manager for measuring execution time."""

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.elapsed_ms = int((time.time() - self.start) * 1000)


print("[base_agent] BaseAgent + Timer loaded")