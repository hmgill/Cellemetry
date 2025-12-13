"""
Agent definition file for ADK CLI (adk web / adk run).
Place this at the package root for: adk web bio_agent
"""
from cellemetry.agents import root_agent

# ADK CLI looks for 'root_agent' or 'agent' at module level
agent = root_agent
