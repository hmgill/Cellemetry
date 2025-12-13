"""
Dependency management using ADK session state.
SAM models and shared resources are stored in state for tool access.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any

@dataclass
class AnalysisDeps:
    """Container for analysis dependencies - stored in session state."""
    sam_model: Any
    sam_processor: Any
    image_path: Path
    device: str
    pixel_size_microns: Optional[float] = None

    def to_state_dict(self) -> dict:
        """Convert to dict for session state storage."""
        return {
            "app:sam_model": self.sam_model,
            "app:sam_processor": self.sam_processor,
            "app:image_path": str(self.image_path),
            "app:device": self.device,
            "app:pixel_size_microns": self.pixel_size_microns,
        }

def get_deps_from_state(state: dict) -> AnalysisDeps:
    """Reconstruct AnalysisDeps from session state."""
    return AnalysisDeps(
        sam_model=state.get("app:sam_model"),
        sam_processor=state.get("app:sam_processor"),
        image_path=Path(state.get("app:image_path")),
        device=state.get("app:device", "cpu"),
        pixel_size_microns=state.get("app:pixel_size_microns"),
    )
