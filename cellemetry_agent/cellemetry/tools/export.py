"""
Data export tools (Excel, CSV, etc.).
"""
from typing import Optional
from google.adk.tools.tool_context import ToolContext

from ..services import analysis


def save_excel_tool(
    filename: str,
    cell_stats: Optional[dict] = None,
    nuc_stats: Optional[dict] = None,
    spatial_stats: Optional[dict] = None,
    rel_stats: Optional[dict] = None,
    tool_context: ToolContext = None
) -> dict:
    """
    Save all statistics to a multi-sheet Excel file.
    
    Args:
        filename: Base filename for the output Excel file
        cell_stats: Optional cell morphology stats
        nuc_stats: Optional nuclei morphology stats
        spatial_stats: Optional spatial distribution stats
        rel_stats: Optional relationship stats
        tool_context: Automatically injected by ADK
    
    Returns:
        dict with the output filepath
    """
    result = analysis.save_stats_to_excel(
        filename, cell_stats, nuc_stats, spatial_stats, rel_stats
    )
    return {"excel_path": result}
