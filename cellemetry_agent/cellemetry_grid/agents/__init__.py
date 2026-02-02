"""
Agents package for bio_agent.
Exports the agent hierarchy with manager as root.
"""
from .analyst import analyst_agent
from .manager import manager_agent

# The root agent for ADK runner
root_agent = manager_agent

__all__ = [
    "root_agent",
    "manager_agent",
    "analyst_agent",
]
