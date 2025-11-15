"""
Base Agent Interface
Person B - Hour 1-2: Agent Interface

Defines the standard interface that all agents must implement.
Based on PRD Section 4.1.
"""

from typing import Protocol, Any, Optional
from pydantic import BaseModel, Field


class AgentInput(BaseModel):
    """
    Base input model for all agents.

    Attributes:
        session_id: Unique identifier for the generation session
        data: Agent-specific input data (prompts, config, etc.)
        metadata: Optional metadata for tracking and logging
    """
    session_id: str = Field(..., description="Session ID for tracking")
    data: dict[str, Any] = Field(..., description="Agent-specific input data")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional metadata for tracking"
    )


class AgentOutput(BaseModel):
    """
    Base output model for all agents.

    Attributes:
        success: Whether the agent execution succeeded
        data: Agent-specific output data (results, URLs, etc.)
        cost: Estimated cost in USD for this agent execution
        duration: Time taken in seconds
        error: Error message if execution failed
    """
    success: bool = Field(..., description="Whether execution succeeded")
    data: dict[str, Any] = Field(..., description="Agent-specific output data")
    cost: float = Field(..., description="Cost in USD", ge=0.0)
    duration: float = Field(..., description="Duration in seconds", ge=0.0)
    error: Optional[str] = Field(
        default=None,
        description="Error message if failed"
    )


class Agent(Protocol):
    """
    Standard interface that all agents must implement.

    This is a Protocol (duck typing) rather than an ABC to allow
    flexibility in implementation while maintaining a standard interface.
    """

    async def process(self, input: AgentInput) -> AgentOutput:
        """
        Process the input and return output.

        Args:
            input: Agent input containing session_id and data

        Returns:
            AgentOutput with results, cost, and duration

        Raises:
            Exception: If agent execution fails critically
        """
        ...
