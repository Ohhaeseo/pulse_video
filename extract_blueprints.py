"""
extract_blueprints.py
레퍼런스 영상을 Gemini 비전 모델로 분석하여, 
카메라 앵글, 조명, 렌즈 효과 등의 '제작 블루프린트(Blueprint)' JSON을 추출하는 유틸리티 스크립트입니다.
"""
import os
import time
import json
import logging
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Verify API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env")

client = genai.Client(api_key=api_key)

REFERENCES_DIR = "static/references"
DB_FILE = "reference_blueprints.json"

PROMPT = """
You are an elite Hollywood DP and SNS Video Marketer. Watch this short reference video and dissect its EXACT camera directing blueprint for a Vertex AI VEO 2.0 generation template.

Output ONLY valid JSON matching this exact structure, with no markdown wrappers or extra text:
{
  "concept": "A 3-word summary of the subject",
  "target_vibe": "Choose exactly ONE: [에너지 (SNS Viral 릴스/쇼츠 스타일, 빠른 템포 훅) / 프리미엄 (CF 광고 스타일, 고급 시네마틱 렌즈 워크) / 무드 (인스타그램 감성 스토리, 따뜻한 렌즈 플레어)]",
  "sns_marketing_hook": "How does the first 2 seconds grab attention visually? (English)",
  "camera_angle": "List exact angles used (e.g., Extreme Close-up, Low angle tracking) (English)",
  "lens_optical_effects": "List exact lenses/effects used (e.g., 85mm, rack focus, cinematic bokeh, macro) (English)",
  "visual_keywords": "List 4-5 visual mood keywords (e.g., Luxurious, Moody neon, High contrast) (English)",
  "reference_style_blueprint": "[REFERENCE CLIP ANALYSIS] Write a 3-sentence intense analysis of the camera pacing, lighting, and movement. (English)"
}
"""

def extract_video_blueprint(filepath):
    filename = os.path.basename(filepath)
    video_id = os.path.splitext(filename)[0]
    fname_lower = filename.lower()
    
    forced_vibe = "무드 (인스타그램 감성 스토리, 따뜻한 렌즈 플레어)" # default
    if "premium" in fname_lower or "luxury" in fname_lower:
        forced_vibe = "프리미엄 (CF 광고 스타일, 고급 시네마틱 렌즈 워크)"
    elif "energy" in fname_lower or "bar" in fname_lower:
        forced_vibe = "에너지 (SNS Viral 릴스/쇼츠 스타일, 빠른 템포 훅)"
    elif "mood" in fname_lower or "cafe" in fname_lower:
        forced_vibe = "무드 (인스타그램 감성 스토리, 따뜻한 렌즈 플레어)"

    logger.info(f"📤 Uploading {filename} to Gemini... (Forced Vibe: {forced_vibe})")
    try:
        video_file = client.files.upload(file=filepath)
        
        # Wait for processing
        while video_file.state.name == "PROCESSING":
            logger.info("⏳ Waiting for video processing...")
            time.sleep(5)
            video_file = client.files.get(name=video_file.name)
            
        if video_file.state.name == "FAILED":
            logger.error(f"❌ Video processing failed for {filename}")
            return None
            
        logger.info(f"✅ Video ready! Analyzing {filename}...")
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[video_file, PROMPT],
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json"
            )
        )
        
        raw_json = response.text.strip()
        data = json.loads(raw_json)
        
        # Build the full 14-field struct for DSPy
        return {
            "id": video_id,
            "concept": data.get("concept", "A cinematic scene"),
            "target_vibe": forced_vibe,
            "target_persona": "A focused customer",
            "sns_marketing_hook": data.get("sns_marketing_hook", ""),
            "camera_angle": data.get("camera_angle", ""),
            "lens_optical_effects": data.get("lens_optical_effects", ""),
            "visual_keywords": data.get("visual_keywords", ""),
            "food_focus_rule": "Focus heavily on texture and lighting. If a human is present, they MUST be an ordinary Korean adult acting surprised. NO EATING.",
            "negative_constraints": "blurry, text overlay, eating, chewing",
            "image_visual_context": "Placeholder for dynamic user image",
            "reference_style_blueprint": data.get("reference_style_blueprint", ""),
            "rationale": "Mimicking the uploaded reference video precisely.",
            "final_veo_json": "{}",
            "audio_script": "분위기 있는 영상입니다."
        }
        
    except Exception as e:
        logger.error(f"⚠️ Error analyzing {filename}: {e}")
        return None

def main():
    if not os.path.exists(REFERENCES_DIR):
        logger.error(f"Directory {REFERENCES_DIR} not found.")
        return

    # Load existing DB
    db = {"reference_videos": []}
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try:
                db = json.load(f)
            except:
                pass
                
    existing_ids = {item["id"] for item in db.get("reference_videos", [])}
    new_entries = []

    for filename in os.listdir(REFERENCES_DIR):
        if not filename.lower().endswith(".mp4"):
            continue
            
        video_id = os.path.splitext(filename)[0]
        if video_id in existing_ids:
            logger.info(f"⏭️ Skipping {filename}, already exists in DB.")
            continue
            
        filepath = os.path.join(REFERENCES_DIR, filename)
        blueprint = extract_video_blueprint(filepath)
        
        if blueprint:
            new_entries.append(blueprint)
            existing_ids.add(video_id)
            
    if new_entries:
        db["reference_videos"].extend(new_entries)
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=2)
        logger.info(f"🎉 Successfully added {len(new_entries)} new blueprints to {DB_FILE}!")
    else:
        logger.info("✅ No new videos to extract.")

if __name__ == "__main__":
    main()
