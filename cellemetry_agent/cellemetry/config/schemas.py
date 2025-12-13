"""
Pydantic schemas for structured inputs/outputs.
ADK supports Pydantic models for structured output via output_schema.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict


# --- SAM3 Inputs ---
class BoundingBox(BaseModel):
    ymin: int = Field(description="Top Y (0-1000)")
    xmin: int = Field(description="Left X (0-1000)")
    ymax: int = Field(description="Bottom Y (0-1000)")
    xmax: int = Field(description="Right X (0-1000)")


class ComponentRequest(BaseModel):
    entity: str = Field(description="Generic object name (e.g., 'cell'). 1 word.")
    color: str = Field(description="Dominant color adjective (e.g., 'green').")
    morphology: str = Field(description="Dominant shape adjective (e.g., 'irregular').")
    bboxes: List[BoundingBox]


# --- Stats Schemas ---
class BasicStats(BaseModel):
    count: int
    area_mean: float
    area_std: float
    unit: str = "px²"


class SpatialStats(BaseModel):
    avg_nnd: float
    std_nnd: float
    density: float
    avg_neighbor_count: float
    std_neighbor_count: float
    dist_unit: str = "px"
    density_unit: str = "N/A"


class RelationalStats(BaseModel):
    matched_pairs: int
    avg_ratio: float
    std_ratio: float


# --- Analyst Output ---
class SegmentedComponent(BaseModel):
    label: str
    description: str
    mask_filename: str
    data_filename: str
    count: int


class AnalystResult(BaseModel):
    """Structured output from the Analyst agent."""
    pixel_size_used: Optional[float] = None
    components_found: List[SegmentedComponent] = Field(default_factory=list)
    excel_path: str = ""
    cell_stats: Optional[BasicStats] = None
    nuclei_stats: Optional[BasicStats] = None
    spatial_stats: Optional[SpatialStats] = None
    relational_stats: Optional[RelationalStats] = None


# --- Manager Output ---
class ManagerSummary(BaseModel):
    """Final user-facing summary from the Manager."""
    executive_summary: str
    key_findings: List[str]
    file_locations: Dict[str, str] = Field(
        default_factory=dict,
        description="Map of 'description' to 'filepath'"
    )
