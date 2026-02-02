"""
Dependency management using ADK session state.
SAM models and shared resources are stored in state for tool access.
Acts as the Source of Truth for where files go.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Any
import os

@dataclass
class AnalysisDeps:
    """
    Container for analysis dependencies and session context.
    """
    sam_model: Any
    sam_processor: Any
    image_path: Path
    output_dir: Path  # <--- NEW: Centralized output folder
    device: str
    pixel_size_microns: Optional[float] = None

    def get_output_path(self, filename: str) -> str:
        """Helper to get full path for a file in the run directory."""
        return str(self.output_dir / filename)

    def to_state_dict(self) -> dict:
        """Convert to dict for session state storage."""
        return {
            "app:sam_model": self.sam_model,
            "app:sam_processor": self.sam_processor,
            "app:image_path": str(self.image_path),
            "app:output_dir": str(self.output_dir),
            "app:device": self.device,
            "app:pixel_size_microns": self.pixel_size_microns,
        }

def get_deps_from_state(state: dict) -> AnalysisDeps:
    """Reconstruct AnalysisDeps from session state."""
    # Ensure output dir exists if passed in state (safety check)
    out_dir = Path(state.get("app:output_dir", "."))
    out_dir.mkdir(parents=True, exist_ok=True)

    return AnalysisDeps(
        sam_model=state.get("app:sam_model"),
        sam_processor=state.get("app:sam_processor"),
        image_path=Path(state.get("app:image_path")),
        output_dir=out_dir,
        device=state.get("app:device", "cpu"),
        pixel_size_microns=state.get("app:pixel_size_microns"),
    )
