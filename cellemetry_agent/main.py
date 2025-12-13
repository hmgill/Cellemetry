"""
Main entry point with streaming support.
Uses ADK InMemoryRunner with async streaming.
"""
import asyncio
import torch

from pathlib import Path
from dotenv import load_dotenv
from transformers import Sam3Processor, Sam3Model

from google.adk.runners import InMemoryRunner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from cellemetry import root_agent, AnalysisDeps


load_dotenv()


APP_NAME = "cellemetry"
USER_ID = "user_1"


async def run_analysis_streaming(
    image_path: Path,
    user_prompt: str,
    deps: AnalysisDeps,
) -> None:
    """
    Run the analysis with streaming output.
    
    Args:
        image_path: Path to the image file
        user_prompt: User's analysis request
        deps: Analysis dependencies (SAM model, etc.)
    """
    # Initialize runner and session service
    runner = InMemoryRunner(agent=root_agent, app_name=APP_NAME)
    session_service = runner.session_service
    
    # Create session with deps stored in state
    initial_state = deps.to_state_dict()
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        state=initial_state,
    )    
    print(f"\n🤖 Manager received prompt: '{user_prompt}'")
    print("=" * 50)
    
    # Build multimodal content (text + image)
    image_bytes = image_path.read_bytes()
    content = types.Content(
        role="user",
        parts=[
            types.Part(text=user_prompt),
            types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
        ]
    )
    
    # Stream events from the agent
    print("\n📡 Streaming agent events...\n")
    
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session.id,
        new_message=content,
    ):
        # Process streaming events
        author = event.author
        
        # Log tool calls
        if event.get_function_calls():
            for fc in event.get_function_calls():
                print(f"  🔧 [{author}] Calling tool: {fc.name}")
        
        # Log text responses
        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    # For streaming, partial=True means it's still generating
                    if event.partial:
                        print(f"  💬 [{author}] (streaming): {part.text[:100]}...")
                    else:
                        print(f"  ✅ [{author}] Complete response received")
        
        # Check for final response
        if event.is_final_response():
            print(f"\n🏁 Final response from: {author}")
    
    # Retrieve final state and output
    final_session = await session_service.get_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session.id,
    )

    # Extract results from state
    print("\n" + "=" * 50)
    print("📋 FINAL REPORT")
    print("=" * 50)
    
    manager_output = final_session.state.get("manager_summary")
    if manager_output:
        if hasattr(manager_output, 'executive_summary'):
            print(f"\n>> EXECUTIVE SUMMARY:\n{manager_output.executive_summary}")
            print("\n>> KEY FINDINGS:")
            for finding in manager_output.key_findings:
                print(f" - {finding}")
            print("\n>> OUTPUT FILES:")
            for desc, path in manager_output.file_locations.items():
                print(f" - {desc}: {path}")
        else:
            # Raw dict/string output
            print(f"\n{manager_output}")


async def main():
    """Main entry point."""
    image_path = Path('105520269.s1.png')
    
    user_prompt = (
        "I have an image with 0.27 microns/pixel resolution. "
        "Please identify the green irregular cells and blue round nuclei. "
        "I need a full statistical report on their morphology and spatial density."
    )
    
    print("--- Loading Models ---")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Note: Replace with actual SAM3 loading when available
    # For now, placeholder to show structure
    try:
        sam_model = Sam3Model.from_pretrained("facebook/sam3").to(device)
        sam_processor = Sam3Processor.from_pretrained("facebook/sam3")
    except ImportError:
        print("⚠️  SAM3 not available, using placeholder")
        sam_model = None
        sam_processor = None
    
    deps = AnalysisDeps(
        sam_model=sam_model,
        sam_processor=sam_processor,
        image_path=image_path,
        device=device,
        pixel_size_microns=None,  # Let agent parse from prompt
    )
    
    await run_analysis_streaming(image_path, user_prompt, deps)


if __name__ == "__main__":
    asyncio.run(main())
