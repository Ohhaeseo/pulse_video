import os
import time
import logging
from typing import Optional, Dict, Any
from lumaai import LumaAI
from services.llm_service import LLMService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LumaService:
    def __init__(self):
        self.api_key = os.getenv("LUMA_API_KEY")
        if not self.api_key:
            logger.error("❌ LUMA_API_KEY is missing!")
        
        # Initialize Luma Client
        self.client = LumaAI(auth_token=self.api_key)
        
        # Reuse existing LLM Service for prompt optimization
        self.llm_service = LLMService()

    async def generate_video(self, payload: Dict[str, Any], image_path: Optional[str] = None) -> str:
        """
        Generate a video using Luma Dream Machine API.
        """
        logger.info("🎬 Luma Service: Starting Generation Process...")
        
        try:
            # 1. Optimize Prompt with LLM (reusing the logic from VeoService)
            # This ensures we get the detailed visual descriptions
            optimized_payload = await self.llm_service.optimize_payload(payload, image_path=image_path)
            
            metadata = optimized_payload.get("metadata", {})
            timeline = optimized_payload.get("timeline", [])
            key_elements = optimized_payload.get("key_elements", [])
            base_style = metadata.get("base_style", "")
            location = metadata.get("location", "")
            
            timeline_desc = " ".join([f"[{scene.get('section')}]: {scene.get('action')}" for scene in timeline])
            
            # Construct a single rich text prompt for Luma
            final_prompt = (
                f"Vertical video (9:16). {base_style}. "
                f"Setting: {location}. "
                f"Key Elements: {', '.join(key_elements)}. "
                f"Action Flow: {timeline_desc}"
            )
            
            logger.info(f"✨ Final Prompt for Luma: {final_prompt}")

            # 2. Call Luma API
            # Note: Luma currently supports text-to-video primarily via SDK simple interface.
            # Local image upload logic would require a publicly accessible URL in most cases.
            # We will proceed with Text-to-Video using the rich description derived from the image (via LLM).
            
            generation = self.client.generations.create(
                prompt=final_prompt,
                aspect_ratio="9:16",
                loop=False,
                model="ray-2" # Explicitly specify model
            )
            
            gen_id = generation.id
            logger.info(f"🚀 Luma Generation Started: {gen_id}")
            
            # 3. Poll for completion
            start_time = time.time()
            while True:
                # Timeout check (5 minutes)
                if time.time() - start_time > 300:
                    raise TimeoutError("Luma generation timed out")
                
                gen_status = self.client.generations.get(id=gen_id)
                state = gen_status.state
                
                if state == "completed":
                    video_url = gen_status.assets.video
                    logger.info(f"✅ Luma Generation Completed! URL: {video_url}")
                    return video_url
                elif state == "failed":
                    failure_reason = gen_status.failure_reason
                    logger.error(f"❌ Luma Generation Failed: {failure_reason}")
                    raise Exception(f"Luma Generation Failed: {failure_reason}")
                
                logger.info(f"⏳ Luma Generating... Status: {state}")
                time.sleep(4) # Poll every 4 seconds
                
        except Exception as e:
            logger.error(f"❌ Luma Service Error: {e}")
            raise e
