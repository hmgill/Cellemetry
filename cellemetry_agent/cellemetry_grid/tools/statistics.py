"""
Statistical analysis tools for morphology and spatial metrics.
"""
from typing import Optional
from google.adk.tools.tool_context import ToolContext

from ..config.dependencies import get_deps_from_state
from ..config.schemas import ComprehensiveStats
from ..services import analysis


def compute_comprehensive_stats(
    cell_file: Optional[str] = None,
    nuc_file: Optional[str] = None,
    tool_context: ToolContext = None
) -> ComprehensiveStats:
    """
    Calculate morphology, spatial, and relational statistics in a single pass.
    
    Args:
        cell_file: Path to the .npz mask file for Cells (optional)
        nuc_file: Path to the .npz mask file for Nuclei (optional)
        tool_context: Automatically injected by ADK
    
    Returns:
        ComprehensiveStats object containing all computed statistics.
    """
    deps = get_deps_from_state(tool_context.state)
    pixel_scale = deps.pixel_size_microns
    
    stats = ComprehensiveStats()

    # 1. Analyze Cells (Morphology + Spatial)
    if cell_file:
        stats.cell_stats = analysis.get_basic_stats(
            cell_file, pixel_scale=pixel_scale
        )
        stats.spatial_stats = analysis.get_spatial_stats(
            cell_file, pixel_scale=pixel_scale
        )
    
    # 2. Analyze Nuclei (Morphology only)
    if nuc_file:
        stats.nuclei_stats = analysis.get_basic_stats(
            nuc_file, pixel_scale=pixel_scale
        )

    # 3. Analyze Relationships (Overlap)
    if cell_file and nuc_file:
        stats.relational_stats = analysis.analyze_relationships(
            cell_file, nuc_file
        )

    return stats
