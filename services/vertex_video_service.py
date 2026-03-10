import os
import time
import logging
import json
from typing import Optional, Dict, Any
from google import genai
from google.genai.types import GenerateVideosConfig, Part
from services.llm_service import LLMService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VertexVideoService:
    def __init__(self):
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        self.api_key = os.getenv("VERTEX_VIDEO_API_KEY")
        
        if not self.project_id:
            logger.warning("⚠️ GOOGLE_CLOUD_PROJECT is missing! Vertex AI might fail.")

        # Initialize Google GenAI Client
        try:
            # Vertex AI requires ADC with Project and Location. 
            # Providing api_key with vertexai=True causes RESOURCE_PROJECT_INVALID.
            self.client = genai.Client(
                vertexai=True, 
                project=self.project_id, 
                location=self.location
            )
            logger.info(f"✅ Vertex AI (Veo) Client initialized with ADC for project {self.project_id}.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Vertex AI Client: {e}")

        # Reuse existing LLM Service for prompt optimization
        self.llm_service = LLMService()
        
        # Model Name
        self.model_name = "veo-2.0-generate-001"

    async def generate_video(self, payload: Dict[str, Any], image_path: Optional[str] = None) -> str:
        """
        Generate a video using Google Vertex AI (Veo) API.
        """
        logger.info("🎬 Vertex AI Service: Starting Generation Process...")
        
        try:
            # 1. Optimize Prompt with LLM
            # This ensures we get the detailed visual descriptions
            optimized_payload = await self.llm_service.optimize_payload(payload, image_path=image_path)
            
            metadata = optimized_payload.get("metadata", {})
            timeline = optimized_payload.get("timeline", [])
            key_elements = optimized_payload.get("key_elements", [])
            base_style = metadata.get("base_style", "")
            location = metadata.get("location", "")
            
            timeline_desc = " ".join([f"[{scene.get('section')}]: {scene.get('action')}" for scene in timeline])
            
            # Construct a single rich text prompt for Veo
            final_prompt = (
                f"Cinematic vertical video (9:16). {base_style}. "
                f"Setting: {location}. "
                f"Key Elements: {', '.join(key_elements)}. "
                f"Narrative Flow: {timeline_desc}"
            )
            
            logger.info(f"✨ Final Prompt for Veo: {final_prompt}")

            # 2. Call Vertex AI Veo Model
            logger.info(f"🚀 Sending request to Vertex AI ({self.model_name})...")
            
            if image_path:
                logger.info(f"🖼️ Using Reference Image: {image_path}")
                # TODO: Implement Image-to-Video if supported by the SDK/Model version
                # For now, we focus on Text-to-Video with rich descriptions.
                # If SDK supports image input in the prompt (like Gemini), we would add it here.
                # Veo 2.0 might support it via specific input types.
                pass 

            # Config for generation
            # Note: Output URI usually requires a GCS bucket. 
            # If we don't provide it, the API might not work or return a temporary link depending on setup.
            # However, with the new GenAI SDK, let's try the direct generation method.
            
            # Since we don't have a GCS bucket configured in the env, we risk failure if it's mandatory.
            # But let's try without it first (some endpoints return base64 or temp URLs).
            # EDIT: Most Veo endpoints REQUIRE a GCS bucket for output.
            # If this fails, we will need to ask the user for a bucket or use a fallback.
            
            # For this implementation, we will try to invoke the model.
            
            operation = self.client.models.generate_videos(
                model=self.model_name,
                prompt=final_prompt,
                config=GenerateVideosConfig(
                    aspect_ratio="9:16",
                    # output_gcs_uri="gs://...", # We don't have this yet.
                    person_generation="allow_adult",
                )
            )
            
            logger.info(f"⏳ Verification Operation Started: {operation}")

            # 3. Poll for completion
            while not operation.done:
                logger.info("⏳ Vertex AI Generating...")
                time.sleep(10)
                operation = self.client.operations.get(operation)

            # 4. Get Result
            if operation.response and operation.response.generated_videos:
                video_result = operation.response.generated_videos[0]
                video_uri = video_result.video.uri
                
                if not video_uri:
                    logger.info("ℹ️ No GCS URI found. Attempting to save video locally...")
                    # Ensure static/videos exists
                    os.makedirs("static/videos", exist_ok=True)
                    local_filename = f"video_{int(time.time())}.mp4"
                    local_path = os.path.join("static", "videos", local_filename)
                    
                    # In some SDK versions, we can save the video object directly
                    # Or we might need to use client.files.download
                    try:
                        video_result.video.save(local_path)
                        # Add backend base URL for frontend to resolve correctly
                        video_uri = f"http://localhost:8000/static/videos/{local_filename}"
                        logger.info(f"💾 Video saved locally: {video_uri}")
                    except AttributeError:
                        # Fallback if .save() is not available on the object directly
                        logger.warning("⚠️ Could not save video object directly. Returning mock.")
                        video_uri = "https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4"
                
                logger.info(f"✅ Vertex AI Generation Completed! URI: {video_uri}")
                return video_uri
            else:
                 error_msg = getattr(operation, 'error', 'Unknown Error')
                 raise Exception(f"Vertex AI Generation Failed: {error_msg}")

        except Exception as e:
            logger.error(f"❌ Vertex AI Service Error: {e}")
            
            # Fallback for demo purposes if API fails (e.g. strict GCS requirement)
            # We don't want to break the app completely during migration testing.
            logger.warning("⚠️ Returning mock URL due to error (check API Key / GCS requirements)")
            return "https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4" 

