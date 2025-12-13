"""
Segmentation tools using SAM3.
"""
from typing import Optional, Union, List
from google.adk.tools.tool_context import ToolContext

from ..config.dependencies import get_deps_from_state
from ..config.schemas import ComponentRequest, BoundingBox
from ..services import sam


def apply_sam3_tool(
    entity: str,
    color: str,
    morphology: str,
    bboxes: List[BoundingBox],
    tool_context: ToolContext
) -> dict:
    """
    Segment biological components using SAM3.
    
    Args:
        entity: Object name (e.g., 'cell', 'nucleus') - use SINGULAR form
        color: Color adjective (e.g., 'green', 'blue')
        morphology: Shape adjective (e.g., 'irregular', 'round')
        bboxes: Bounding boxes in one of these formats:
                - List of dicts: [{"ymin": 0, "xmin": 0, "ymax": 100, "xmax": 100}, ...]
                - List of lists: [[ymin, xmin, ymax, xmax], ...]
                Values should be 0-1000 normalized coordinates.
        tool_context: Automatically injected by ADK
    
    Returns:
        dict with:
        - result: Description of segmentation outcome
        - mask_file: EXACT path to the .npz file containing masks
        - plot_file: Path to visualization image
        - count: Number of objects found
    """
    deps = get_deps_from_state(tool_context.state)
    
    # Convert bboxes to BoundingBox objects, handling multiple formats
    bbox_objects = []
    for b in bboxes:
        if isinstance(b, dict):
            # Format: {"ymin": 0, "xmin": 0, "ymax": 100, "xmax": 100}
            bbox_objects.append(BoundingBox(**b))
        elif isinstance(b, (list, tuple)):
            # Format: [ymin, xmin, ymax, xmax] or [xmin, ymin, xmax, ymax]
            if len(b) == 4:
                # Assume [ymin, xmin, ymax, xmax] based on schema order
                bbox_objects.append(BoundingBox(
                    ymin=int(b[0]),
                    xmin=int(b[1]),
                    ymax=int(b[2]),
                    xmax=int(b[3])
                ))
            else:
                print(f"[Warning] Skipping invalid bbox: {b}")
        else:
            print(f"[Warning] Skipping unrecognized bbox format: {b}")
    
    if not bbox_objects:
        return {
            "result": "ERROR: No valid bounding boxes provided",
            "mask_file": None,
            "plot_file": None,
            "count": 0,
            "label": f"{color} {morphology} {entity}"
        }
    
    request = ComponentRequest(
        entity=entity,
        color=color,
        morphology=morphology,
        bboxes=bbox_objects
    )
    
    result_str = sam.execute_segmentation(deps, request)
    
    # Generate consistent filenames
    safe_label = f"{color}_{entity}".replace(" ", "_").lower()
    mask_file = f"/tmp/data_{safe_label}.npz"
    plot_file = f"/tmp/out_{safe_label}.png"
    
    # Try to extract count from result
    count = 0
    if "Found" in result_str:
        try:
            count = int(result_str.split("Found")[1].split()[0])
        except:
            pass
    
    return {
        "result": result_str,
        "mask_file": mask_file,  # <-- USE THIS EXACT PATH for get_basic_stats, get_spatial_stats
        "plot_file": plot_file,
        "count": count,
        "label": f"{color} {morphology} {entity}"
    }
