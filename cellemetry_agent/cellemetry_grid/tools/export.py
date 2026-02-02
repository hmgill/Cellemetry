"""
Data export tools (Excel, CSV, etc.).
"""
import os
from typing import Optional
from google.adk.tools.tool_context import ToolContext

from ..config.dependencies import get_deps_from_state
from ..config.schemas import (
    ExportResult, 
    BasicStats, 
    SpatialStats, 
    RelationalStats
)
from ..services import analysis


def save_excel_tool(
    filename: str,
    cell_stats: Optional[BasicStats] = None,
    nuc_stats: Optional[BasicStats] = None,
    spatial_stats: Optional[SpatialStats] = None,
    rel_stats: Optional[RelationalStats] = None,
    tool_context: ToolContext = None
) -> ExportResult:
    """
    Save all statistics to a multi-sheet Excel file.
    """
    deps = get_deps_from_state(tool_context.state)
    
    # Force filename to be in the correct output directory
    if not filename.endswith(".xlsx"):
        filename += ".xlsx"
    
    base_name = os.path.basename(filename)
    full_path = deps.get_output_path(base_name)
    
    # Convert Pydantic models to dicts for the service layer
    # The service layer (analysis.py) expects dicts or None
    c_dict = cell_stats.model_dump() if cell_stats else None
    n_dict = nuc_stats.model_dump() if nuc_stats else None
    s_dict = spatial_stats.model_dump() if spatial_stats else None
    r_dict = rel_stats.model_dump() if rel_stats else None
    
    result_path = analysis.save_stats_to_excel(
        full_path, c_dict, n_dict, s_dict, r_dict
    )
    
    return ExportResult(excel_path=result_path)
