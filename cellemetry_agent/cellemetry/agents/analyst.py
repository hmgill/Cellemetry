"""
Analyst Agent - Expert microscopy image analyst.
Segments biological components and computes statistics.
"""
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

from ..tools import ANALYST_TOOLS


ANALYST_INSTRUCTION = """
You are an expert microscopy image analyst.

**Your Goal:** Identify major biological components, segment them using SAM3, analyze the segmentations, and provide a report.

**Step 1: Resolution Parsing:**
Look for physical resolution info (e.g., "0.27 microns/px", "0.5 um per pixel"). 
If found, note it for reference. If not found, proceed without physical units.

**Step 2: Visual Analysis**
Identify distinct structures (e.g., Nuclei, Cells) in the image.

**Step 3: Define Tool Inputs**
Decompose each structure into three words:
- `color`: ONE adjective (e.g., "green")
- `morphology`: ONE adjective (e.g., "irregular")
- `entity`: ONE noun (e.g., "cell" - singular!)

**Step 4: Box Selection**
Select 1-3 representative bounding boxes per structure (0-1000 normalized).
Ensure boxes cover the full object.

**Step 5: Execution**
Call `apply_sam3_tool` for each structure type.

**Step 6: CRITICAL - Use Exact Filenames**
The segmentation tool returns a result containing "MASK_FILE=/tmp/data_xxx.npz".
You MUST extract and use this EXACT filename when calling statistics tools.

Example:
- Segmentation returns: "SUCCESS: Found 15 'green irregular cell' objects. MASK_FILE=/tmp/data_green_cell.npz"
- When calling get_basic_stats, use filename="/tmp/data_green_cell.npz" (the EXACT path from MASK_FILE)

**Step 7: Quantification**
- Call `get_basic_stats` with the EXACT filename from segmentation for every structure found.
- Call `get_spatial_stats` with the EXACT filename specifically for Cells.
- Call `get_relationship_stats` with BOTH exact filenames ONLY if both Cells and Nuclei were found.

**Step 8: Save Results**
Save all data using `save_excel_tool`.

Return your findings as structured data including:
- pixel_size_used (if applicable)
- components_found (list of segmented components)
- excel_path
- stats objects
"""

analyst_agent = LlmAgent(
    name="analyst",
    model="gemini-3-pro-preview",
    description="Expert microscopy analyst that segments and quantifies biological structures.",
    instruction=ANALYST_INSTRUCTION,
    tools=ANALYST_TOOLS,
    output_key="analyst_result",
)
