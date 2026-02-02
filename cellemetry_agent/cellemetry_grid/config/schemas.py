"""
Pydantic schemas for structured inputs/outputs.
ADK supports Pydantic models for structured output via output_schema.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict


# --- Core Geometric Types ---
class BoundingBox(BaseModel):
    ymin: int = Field(..., description="Top Y (0-1000)")
    xmin: int = Field(..., description="Left X (0-1000)")
    ymax: int = Field(..., description="Bottom Y (0-1000)")
    xmax: int = Field(..., description="Right X (0-1000)")


# --- Tool Input Schemas ---
class ComponentRequest(BaseModel):
    entity: str = Field(..., description="Generic object name (e.g., 'cell'). 1 word.")
    color: str = Field(..., description="Dominant color adjective (e.g., 'green').")
    morphology: str = Field(..., description="Dominant shape adjective (e.g., 'irregular').")
    bboxes: List[BoundingBox] = Field(..., description="Representative bounding boxes")


# --- Tool Output Schemas ---
class SegmentationResult(BaseModel):
    label: str
    count: int
    mask_file: str
    plot_file: str
    result_message: str


class ExportResult(BaseModel):
    excel_path: str


# --- Statistical Schemas ---
class BasicStats(BaseModel):
    count: int = 0
    area_mean: float = 0.0
    area_std: float = 0.0
    unit: str = "px²"


class SpatialStats(BaseModel):
    density: float = 0.0
    avg_nnd: float = 0.0
    std_nnd: float = 0.0
    avg_neighbor_count: float = 0.0
    dist_unit: str = "px"
    density_unit: str = "N/A"


class RelationalStats(BaseModel):
    matched_pairs: int = 0
    avg_ratio: float = 0.0
    std_ratio: float = 0.0


class ComprehensiveStats(BaseModel):
    cell_stats: Optional[BasicStats] = None
    nuclei_stats: Optional[BasicStats] = None
    spatial_stats: Optional[SpatialStats] = None
    relational_stats: Optional[RelationalStats] = None


# --- Agent Output Schemas ---
class AnalystResult(BaseModel):
    """Structured output for the Analyst Agent."""
    components_found: List[SegmentationResult] = Field(default_factory=list)
    stats: ComprehensiveStats = Field(default_factory=ComprehensiveStats)
    excel_path: Optional[str] = None
    pixel_size_used: Optional[float] = None


class ManagerSummary(BaseModel):
    """Final output for the Manager Agent."""
    executive_summary: str = Field(..., description="High-level overview of analysis")
    key_findings: List[str] = Field(..., description="Bullet points of biological insights")
    file_locations: Dict[str, str] = Field(..., description="Map of description to file path")
