"""
vertex_video_service.py
Vertex AI의 Veo 모델(veo-2.0-generate-001)을 호출하여 실제 비디오를 생성하는 핵심 서비스입니다.
생성된 영상을 FFmpeg를 사용하여 9:16 비율(쇼츠/릴스용)로 크롭하는 후처리 로직도 포함되어 있습니다.
"""
import os
import time
import logging
import json
from typing import Optional, Dict, Any
from google import genai
from google.genai import types
from google.genai.types import GenerateVideosConfig, Part, VideoGenerationReferenceImage
from services.llm_service import LLMService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VertexVideoService:
    def __init__(self):
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        
        if not self.project_id:
            logger.warning("⚠️ GOOGLE_CLOUD_PROJECT environment variable not set.")
            
        try:
            self.client = genai.Client(
                vertexai=True, 
                project=self.project_id, 
                location=self.location
            )
            logger.info(f"✅ Vertex AI (Veo) Client initialized with ADC for project {self.project_id}.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Vertex AI Client: {e}")

        self.llm_service = LLMService()
        self.model_name = "veo-2.0-generate-001"

    async def generate_video(self, payload: Dict[str, Any], image_path: Optional[str] = None) -> Dict[str, str]:
        print("\n🎬 [Vertex AI Service] Starting Generation Process...")
        logger.info("🎬 Vertex AI Service: Starting Generation Process...")
        
        try:
            optimized_payload = await self.llm_service.optimize_payload(payload, image_path=image_path)
            
            metadata = optimized_payload.get("metadata", {})
            timeline = optimized_payload.get("timeline", [])
            key_elements = optimized_payload.get("key_elements", [])
            base_style = metadata.get("base_style", "")
            location = metadata.get("location", "")
            
            timeline_items = []
            for scene in timeline:
                if isinstance(scene, dict):
                    val = scene.get("action") or scene.get("description") or scene.get("visuals") or scene.get("shot")
                    if val:
                        timeline_items.append(str(val))
                elif isinstance(scene, str):
                    timeline_items.append(scene)
            
            if not timeline_items:
                timeline_items = [str(k) for k in optimized_payload.get("key_elements", []) if k]
                
            timeline_desc = " ".join(timeline_items)
            
            negatives_raw = optimized_payload.get("negative_prompts", [])
            if isinstance(negatives_raw, list):
                negative_prompts = [str(n) for n in negatives_raw if n]
            elif isinstance(negatives_raw, str):
                negative_prompts = [negatives_raw]
            else:
                negative_prompts = []
                
            negative_str = f" DO NOT INCLUDE: {', '.join(negative_prompts)}" if negative_prompts else ""
            
            final_prompt = (
                f"A high-end TikTok/Instagram commercial advertisement (9:16 vertical). "
                f"{timeline_desc} "
                f"Setting: {location}. Lighting & Style: {base_style}. "
                f"Breathtaking cinematography, highly appetizing visuals, ultra-premium commercial quality."
                f"{negative_str}"
            )
            
            print(f"✨ [Vertex AI Service] Final Prompt for Veo prepared.")
            logger.info(f"✨ Final Prompt for Veo: {final_prompt}")

            print(f"🚀 [Vertex AI Service] Sending request to Vertex AI ({self.model_name})...")
            logger.info(f"🚀 Sending request to Vertex AI ({self.model_name})...")
            
            reference_image = None
            if image_path and os.path.exists(image_path):
                print(f"🖼️ [Vertex AI Service] Using Reference Image for Image-to-Video: {image_path}")
                logger.info(f"🖼️ Using Reference Image for Image-to-Video: {image_path}")
                try:
                    with open(image_path, "rb") as img_file:
                        image_bytes = img_file.read()
                    reference_image = types.Image(imageBytes=image_bytes, mimeType="image/jpeg")
                    print("✅ [Vertex AI Service] Image successfully loaded for Veo Video Prompt Payload")
                    logger.info("✅ Image successfully loaded for Veo Video Prompt Payload")
                except Exception as img_err:
                    print(f"⚠️ [Vertex AI Service] Failed to load Reference Image for Veo: {img_err}")
                    logger.error(f"⚠️ Failed to load Reference Image for Veo: {img_err}")
            
            config_params = {
                "aspect_ratio": "16:9",
                "person_generation": "dont_allow"
            }
            
            if reference_image:
                config_params["reference_images"] = [
                    VideoGenerationReferenceImage(
                        image=reference_image,
                        referenceType="ASSET"
                    )
                ]
            
            kwargs = {
                "model": self.model_name,
                "prompt": final_prompt,
                "config": GenerateVideosConfig(**config_params)
            }

            print("⏳ [Vertex AI Service] Veo Verification Operation Started. Please wait...")
            operation = self.client.models.generate_videos(**kwargs)
            logger.info(f"⏳ Verification Operation Started: {operation}")

            while not operation.done:
                print("⏳ [Vertex AI Service] Vertex AI Generating... (Waiting 10s)")
                logger.info("⏳ Vertex AI Generating...")
                time.sleep(10)
                operation = self.client.operations.get(operation)

            if operation.response and operation.response.generated_videos:
                video_result = operation.response.generated_videos[0]
                video_uri = video_result.video.uri
                
                if not video_uri:
                    print("ℹ️ [Vertex AI Service] No GCS URI found. Attempting to save video locally...")
                    logger.info("ℹ️ No GCS URI found. Attempting to save video locally...")
                    os.makedirs("static/videos", exist_ok=True)
                    local_filename = f"video_{int(time.time())}.mp4"
                    local_path = os.path.join("static", "videos", local_filename)
                    
                    try:
                        import subprocess
                        video_result.video.save(local_path)
                        
                        logger.info(f"✂️ Cropping video to 9:16 aspect ratio via FFmpeg...")
                        local_filename_cropped = f"video_9x16_{int(time.time())}.mp4"
                        local_path_cropped = os.path.join("static", "videos", local_filename_cropped)
                        
                        subprocess.run([
                            "ffmpeg", "-y", "-i", local_path, 
                            "-vf", "crop=ih*9/16:ih", 
                            "-c:a", "copy", local_path_cropped
                        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        
                        video_uri = f"http://localhost:8000/static/videos/{local_filename_cropped}"
                        print(f"💾 [Vertex AI Service] Video successfully cropped and saved locally: {video_uri}")
                        logger.info(f"💾 Video cropped and saved locally: {video_uri}")
                        
                        # Cleanup the original 16:9 file
                        try:
                            os.remove(local_path)
                        except:
                            pass
                            
                    except subprocess.CalledProcessError as e:
                        logger.error(f"⚠️ FFmpeg crop failed: {e}. Falling back to 16:9 raw.")
                        video_uri = f"http://localhost:8000/static/videos/{local_filename}"
                    except Exception as e:
                        logger.error(f"⚠️ FFmpeg execution error (missing ffmpeg?): {e}. Falling back to 16:9 raw.")
                        video_uri = f"http://localhost:8000/static/videos/{local_filename}"
                    except AttributeError:
                        print("⚠️ [Vertex AI Service] Could not save video object directly. Returning mock.")
                        logger.warning("⚠️ Could not save video object directly. Returning mock.")
                        video_uri = "https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4"
                
                print(f"✅ [Vertex AI Service] Vertex AI Generation Completed! URI: {video_uri}")
                logger.info(f"✅ Vertex AI Generation Completed! URI: {video_uri}")
                return {"video_url": video_uri}
            else:
                 error_msg = getattr(operation, 'error', 'Unknown Error')
                 raise Exception(f"Vertex AI Generation Failed: {error_msg}")

        except Exception as e:
            logger.error(f"❌ Vertex AI Service Error: {e}")
            logger.warning("⚠️ Returning mock URL due to error (check API Key / GCS requirements)")
            return {
                "video_url": "https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4"
            }
