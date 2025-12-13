import os
import uvicorn
import torch
import asyncio
import requests
import logging
import traceback
from pathlib import Path
from datetime import timedelta
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import Optional, List
import glob

# Google Cloud & Gen AI Imports
from google.cloud import storage
from google.genai import types
from google.adk.runners import InMemoryRunner

# Model Imports
from transformers import Sam3Processor, Sam3Model

# App Imports
from cellemetry import root_agent as agent
from cellemetry.config import AnalysisDeps

# Configure logging for Cloud Run
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variable to hold the heavy model
RUNTIME_DEPS = {}

# Configuration
OUTPUT_BUCKET = os.environ.get("OUTPUT_BUCKET", "cellemetry_bucket")
OUTPUT_PREFIX = os.environ.get("OUTPUT_PREFIX", "outputs")
SIGNED_URL_EXPIRATION_MINUTES = int(os.environ.get("SIGNED_URL_EXPIRATION", 60))
AGENT_TIMEOUT = 300

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the SAM3 model only once when server starts."""
    logger.info("🏗️ Loading SAM3 Model...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Using device: {device}")
    
    try:
        model = Sam3Model.from_pretrained("facebook/sam3").to(device)
        processor = Sam3Processor.from_pretrained("facebook/sam3")
        
        RUNTIME_DEPS["model"] = model
        RUNTIME_DEPS["processor"] = processor
        RUNTIME_DEPS["device"] = device
        logger.info("✅ SAM3 Model Loaded Successfully!")
    except Exception as e:
        logger.warning(f"⚠️ Failed to load SAM3 (Using Mock): {e}")
        RUNTIME_DEPS["model"] = None
        RUNTIME_DEPS["processor"] = None
        RUNTIME_DEPS["device"] = device

    yield
    RUNTIME_DEPS.clear()

app = FastAPI(lifespan=lifespan, title="Cellemetry Agent API", version="1.4")


# Response models
class OutputFile(BaseModel):
    filename: str
    url: str
    content_type: str

class AgentResponse(BaseModel):
    response: str
    structured_summary: Optional[dict] = None
    output_files: List[OutputFile] = []
    error: Optional[str] = None


class AgentRequest(BaseModel):
    prompt: str
    image_url: str = None
    image_filename: str = None
    session_id: str = None  # Optional: for organizing outputs


@app.get("/health")
async def health_check():
    """Health check for Cloud Run."""
    return {
        "status": "healthy",
        "model_loaded": RUNTIME_DEPS.get("model") is not None,
        "device": RUNTIME_DEPS.get("device", "unknown")
    }


@app.get("/")
async def root():
    return {"message": "Cellemetry Agent API", "version": "1.4"}


def download_image(source: str, destination: Path):
    """Downloads image from HTTP URL or GCS Bucket."""
    if source.startswith("gs://"):
        logger.info(f"☁️ Downloading from GCS: {source}")
        try:
            storage_client = storage.Client()
            parts = source[5:].split("/", 1)
            if len(parts) != 2:
                raise ValueError("Invalid GCS URI format")
            
            bucket_name, blob_name = parts
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            blob.download_to_filename(str(destination))
            logger.info(f"✅ Downloaded to {destination}")
            return
        except Exception as e:
            logger.error(f"❌ GCS Download failed: {e}")
            raise RuntimeError(f"GCS Download failed: {e}")

    elif source.startswith("http"):
        logger.info(f"⬇️ Downloading from Web: {source}")
        try:
            resp = requests.get(source, timeout=30)
            resp.raise_for_status()
            destination.write_bytes(resp.content)
            logger.info(f"✅ Downloaded to {destination}")
            return
        except Exception as e:
            logger.error(f"❌ HTTP Download failed: {e}")
            raise RuntimeError(f"HTTP Download failed: {e}")
    
    raise ValueError("Invalid image source. Must start with http://, https://, or gs://")


def upload_outputs_to_gcs(session_id: str) -> List[OutputFile]:
    """
    Upload all output files from /tmp to GCS and return signed URLs.
    
    Args:
        session_id: Unique identifier for this analysis session
        
    Returns:
        List of OutputFile objects with download URLs
    """
    output_files = []
    storage_client = storage.Client()
    bucket = storage_client.bucket(OUTPUT_BUCKET)
    
    # Find all output files in /tmp
    output_patterns = [
        "/tmp/out_*.png",      # Segmentation plots
        "/tmp/data_*.npz",     # Mask data
        "/tmp/*.xlsx",         # Excel reports
    ]
    
    for pattern in output_patterns:
        for filepath in glob.glob(pattern):
            try:
                filename = os.path.basename(filepath)
                blob_path = f"{OUTPUT_PREFIX}/{session_id}/{filename}"
                blob = bucket.blob(blob_path)
                
                # Determine content type
                if filepath.endswith('.png'):
                    content_type = 'image/png'
                elif filepath.endswith('.xlsx'):
                    content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                elif filepath.endswith('.npz'):
                    content_type = 'application/octet-stream'
                else:
                    content_type = 'application/octet-stream'
                
                # Upload file
                blob.upload_from_filename(filepath, content_type=content_type)
                logger.info(f"📤 Uploaded {filename} to gs://{OUTPUT_BUCKET}/{blob_path}")
                
                # Generate signed URL (expires in X minutes)
                signed_url = blob.generate_signed_url(
                    expiration=timedelta(minutes=SIGNED_URL_EXPIRATION_MINUTES),
                    method='GET'
                )
                
                output_files.append(OutputFile(
                    filename=filename,
                    url=signed_url,
                    content_type=content_type
                ))
                
            except Exception as e:
                logger.error(f"❌ Failed to upload {filepath}: {e}")
    
    return output_files


def cleanup_tmp_outputs():
    """Remove output files from /tmp after upload."""
    patterns = ["/tmp/out_*.png", "/tmp/data_*.npz", "/tmp/*.xlsx"]
    for pattern in patterns:
        for filepath in glob.glob(pattern):
            try:
                os.remove(filepath)
            except:
                pass


async def run_agent_with_timeout(runner, session, content, timeout_seconds):
    """Run agent with a timeout wrapper."""
    final_response = ""
    
    async def _run():
        nonlocal final_response
        async for event in runner.run_async(
            session_id=session.id,
            new_message=content,
            user_id="user_1"
        ):
            if event.get_function_calls():
                for fc in event.get_function_calls():
                    logger.info(f"🔧 Tool call: {fc.name}")
            
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        final_response += part.text
        return final_response
    
    try:
        result = await asyncio.wait_for(_run(), timeout=timeout_seconds)
        return result
    except asyncio.TimeoutError:
        logger.error(f"⏰ Agent execution timed out after {timeout_seconds}s")
        raise HTTPException(status_code=504, detail=f"Agent timed out after {timeout_seconds} seconds")


@app.post("/agent/invoke", response_model=AgentResponse)
async def invoke_agent(request: AgentRequest):
    """Run the agent and return results with downloadable file URLs."""
    
    logger.info(f"📥 Received request: prompt='{request.prompt[:50]}...'")
    
    # Generate session ID for organizing outputs
    import uuid
    session_id = request.session_id or str(uuid.uuid4())[:8]
    
    image_path = None
    
    try:
        # 1. ACQUIRE IMAGE
        if request.image_url:
            clean_name = request.image_url.split("/")[-1]
            if "." not in clean_name: 
                clean_name += ".png"
            
            temp_path = Path(f"/tmp/{clean_name}")
            download_image(request.image_url, temp_path)
            image_path = temp_path
            
        elif request.image_filename:
            image_path = Path(request.image_filename)
            if not image_path.exists():
                raise HTTPException(status_code=404, detail=f"Local file '{request.image_filename}' not found.")
        else:
            raise HTTPException(status_code=400, detail="Provide 'image_url' (http/gs) or 'image_filename'")

        logger.info(f"📷 Image acquired: {image_path}")

        # 2. SETUP DEPENDENCIES
        current_deps = AnalysisDeps(
            sam_model=RUNTIME_DEPS.get("model"),
            sam_processor=RUNTIME_DEPS.get("processor"),
            image_path=image_path,
            device=RUNTIME_DEPS.get("device", "cpu"),
            pixel_size_microns=None
        )

        # 3. INITIALIZE SESSION
        runner = InMemoryRunner(agent=agent, app_name="cellemetry")
        
        session = await runner.session_service.create_session(
            app_name="cellemetry",
            user_id="user_1",
            state=current_deps.to_state_dict()
        )
        logger.info(f"✅ Session created: {session.id}")

        # 4. CONSTRUCT MESSAGE
        image_bytes = image_path.read_bytes()
        content = types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=request.prompt),
                types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
            ]
        )

        # 5. RUN AGENT
        logger.info("🤖 Starting agent execution...")
        final_response = await run_agent_with_timeout(
            runner, session, content, AGENT_TIMEOUT
        )
        logger.info("✅ Agent execution complete")

        # 6. UPLOAD OUTPUT FILES TO GCS
        logger.info("📤 Uploading output files to GCS...")
        output_files = upload_outputs_to_gcs(session_id)
        logger.info(f"✅ Uploaded {len(output_files)} files")

        # 7. EXTRACT SUMMARY
        final_state = await runner.session_service.get_session(
            session_id=session.id,
            app_name="cellemetry",
            user_id="user_1"
        )
        summary = final_state.state.get("manager_summary")
        
        structured_summary = None
        if summary:
            if hasattr(summary, 'dict'):
                structured_summary = summary.dict()
            elif hasattr(summary, 'model_dump'):
                structured_summary = summary.model_dump()
            elif isinstance(summary, dict):
                structured_summary = summary
            else:
                structured_summary = {"raw": str(summary)}

        # 8. CLEANUP
        cleanup_tmp_outputs()

        return AgentResponse(
            response=final_response,
            structured_summary=structured_summary,
            output_files=output_files
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        logger.error(traceback.format_exc())
        return AgentResponse(
            response="",
            error=str(e),
            output_files=[]
        )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🚀 Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
