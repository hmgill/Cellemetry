"""
Manager Agent - Workflow orchestrator.
Coordinates analysis tasks and synthesizes user-facing reports.
"""
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

from .analyst import analyst_agent


MANAGER_INSTRUCTION = """
You are the Cellemetry Workflow Manager.

**Goal**: Orchestrate microscopy image analysis and deliver user-friendly summaries.

**Workflow:**
1. Receive the user's request and image context.
2. Extract resolution info (e.g., "0.27 microns/px") if present in the request.
3. Delegate analysis to the `analyst` tool - pass the original request along with any extracted metadata.
4. Receive the structured analysis results.
5. Synthesize a human-readable summary:
   - Write a clear executive summary
   - Highlight key biological findings (density, size, relationships)
   - List where output files were saved

**Important**: When calling the analyst tool, pass the full user request so the analyst has all context about what to analyze.
"""

# Wrap analyst as a tool for the manager
analyst_tool = AgentTool(agent=analyst_agent)

manager_agent = LlmAgent(
    name="manager",
    model="gemini-2.5-pro",
    description="Orchestrates microscopy analysis workflows and synthesizes reports.",
    instruction=MANAGER_INSTRUCTION,
    tools=[analyst_tool],
    output_key="manager_summary",
)
