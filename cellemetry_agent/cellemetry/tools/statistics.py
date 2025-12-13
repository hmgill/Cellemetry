"""
Statistical analysis tools for morphology and spatial metrics.
"""
from google.adk.tools.tool_context import ToolContext

from ..services import analysis


def get_basic_stats(
    filename: str,
    tool_context: ToolContext
) -> dict:
    """
    Calculate basic morphology stats (count, area mean/std).
    
    Args:
        filename: Path to the .npz mask file
        tool_context: Automatically injected by ADK
    
    Returns:
        dict with count, area_mean, area_std, unit
    """
    pixel_scale = tool_context.state.get("app:pixel_size_microns")
    return analysis.get_basic_stats(filename, pixel_scale=pixel_scale)


def get_spatial_stats(
    filename: str,
    tool_context: ToolContext
) -> dict:
    """
    Calculate spatial distribution stats (NND, density, neighbor count).
    
    Args:
        filename: Path to the .npz mask file
        tool_context: Automatically injected by ADK
    
    Returns:
        dict with spatial metrics
    """
    pixel_scale = tool_context.state.get("app:pixel_size_microns")
    return analysis.get_spatial_stats(filename, pixel_scale=pixel_scale)


def get_relationship_stats(
    cell_file: str,
    nuc_file: str,
    tool_context: ToolContext
) -> dict:
    """
    Analyze cell-nucleus relationships (overlap ratios).
    
    Args:
        cell_file: Path to cell masks .npz
        nuc_file: Path to nucleus masks .npz
        tool_context: Automatically injected by ADK
    
    Returns:
        dict with matched_pairs, avg_ratio, std_ratio
    """
    return analysis.analyze_relationships(cell_file, nuc_file)
