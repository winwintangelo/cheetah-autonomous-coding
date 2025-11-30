"""
Coding Agents Package
=====================

This package provides a unified interface for coding agents
to be used in autonomous coding tasks.

Supports 100+ models via OpenRouter API (OpenAI, Google, Meta, Mistral, etc.)
"""

from .base import BaseCodingAgent, AgentConfig, AgentResponse
from .openrouter_agent import OpenRouterAgent

# Registry of available agents
AGENT_REGISTRY = {
    "openrouter": OpenRouterAgent,
}

# Default agent
DEFAULT_AGENT = "openrouter"


def get_agent(agent_type: str, config: AgentConfig) -> BaseCodingAgent:
    """
    Factory function to get the appropriate coding agent.

    Args:
        agent_type: Type of agent (currently only "openrouter" supported)
        config: Agent configuration

    Returns:
        Configured coding agent instance

    Raises:
        ValueError: If agent_type is not supported
    """
    if agent_type not in AGENT_REGISTRY:
        available = ", ".join(AGENT_REGISTRY.keys())
        raise ValueError(
            f"Unknown agent type: {agent_type}. Available agents: {available}"
        )

    agent_class = AGENT_REGISTRY[agent_type]
    return agent_class(config)


def list_available_agents() -> list[str]:
    """Return list of available agent types."""
    return list(AGENT_REGISTRY.keys())


__all__ = [
    "BaseCodingAgent",
    "AgentConfig",
    "AgentResponse",
    "OpenRouterAgent",
    "get_agent",
    "list_available_agents",
    "AGENT_REGISTRY",
    "DEFAULT_AGENT",
]
