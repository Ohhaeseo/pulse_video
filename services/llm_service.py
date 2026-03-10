import os
import json
import logging
import dspy
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VeoPromptSignature(dspy.Signature):
    """
    You are a world-class Video Prompt Engineer specialized in Google VEO 2.0 AI video generation for Korean food promotion.
    Your job is to translate user inputs into breathtaking, visually descriptive English prompts optimized for cinematic AI video generation.
    
    CRITICAL RULES:
    1. Adjust cinematic style, pacing, color grading, and visual keywords HEAVILY based on the `target_vibe`.
    2. Convert abstract Korean personas (e.g., '해장이 필요한 손님') into CONCRETE visual descriptions (e.g., 'A relieved middle-aged Korean man wiping his forehead with a napkin, smiling after finishing a steaming bowl').
    3. Apply the `camera_directing` parameters (lens, aperture, motion) EXACTLY as specified.
    4. STRICTLY ENFORCE `negative_constraints` — these describe what the AI must NEVER generate.
    5. Apply the `food_focus_rule` to ensure the food looks premium and the human behavior is natural and elegant.
    6. Use the `image_visual_context` to match the exact colors, textures, and plating style from the user's uploaded photo.
    7. Output a valid JSON matching the Master Prompt Template structure.
    """
    target_persona = dspy.InputField(desc="The target customer persona described in Korean. Translate into visual English descriptions of a real person.")
    concept = dspy.InputField(desc="The core food concept or menu description in Korean. Translate into appetizing English visual language.")
    target_vibe = dspy.InputField(desc="The overall vibe/style: 에너지 (fast, vibrant, pop), 프리미엄 (slow, luxurious, cinematic), or 무드 (warm, cozy, emotional).")
    
    # Feature 2: Camera Directing
    camera_directing = dspy.InputField(desc="MANDATORY camera setup: specific lens (e.g. 85mm f/1.4), motion type (e.g. dolly push-in), and framing instructions. Apply these EXACTLY in every scene description.")
    style_keywords = dspy.InputField(desc="Visual style keywords that MUST appear throughout the prompt (e.g. 'Slow Motion 120fps, bokeh, candlelight').")
    
    # Feature 3: Negative Constraints
    negative_constraints = dspy.InputField(desc="STRICT list of visual elements that must NEVER appear in the generated video. Include these as explicit avoidance rules in the prompt.")
    food_focus_rule = dspy.InputField(desc="Behavioral rule for how food and humans should be depicted. This rule overrides any default behavior.")
    
    # Feature 4: Vision Pre-processing Context
    image_visual_context = dspy.InputField(desc="Detailed visual analysis of the user's uploaded food photo: colors, textures, lighting, composition, plating style. Use this to ensure the video matches the photo's aesthetic.")
    
    rationale = dspy.OutputField(desc="Think step-by-step: (1) How does the vibe change the mood, speed, and color grading? (2) How do the camera parameters create the right cinematic feel? (3) How do you translate the Korean persona into a natural visual scene? (4) How do you incorporate the food photo's visual details? (5) What negative constraints must be actively avoided?")
    final_veo_json = dspy.OutputField(desc="A valid JSON string containing: title (Korean), hashtags (Korean array), metadata (aspect_ratio, style, vibe_id), key_elements (array), negative_prompts (array from constraints), timeline (array of scene objects with shot_type, description, duration_seconds).")


class LLMService:
    def __init__(self):
        # 1. API 키 및 모델 설정
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("⚠️ 경고: GEMINI_API_KEY가 없습니다.")
        
        # dspy-ai 설정 (Gemini 2.5 Flash를 사용하여 속도 최적화)
        dspy.settings.configure(
            lm=dspy.LM('gemini/gemini-2.5-flash', api_key=self.api_key)
        )
        
        # 기존 클라이언트 속성 (멀티모달 이미지 분석 및 Vision Pre-processing용)
        self.raw_client = genai.Client(api_key=self.api_key)
        
        # 최적화 모듈 설정
        self.optimizer = dspy.ChainOfThought(VeoPromptSignature)

        # 2. 템플릿 로드
        self.templates = {}
        try:
            with open("templates.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                for t in data.get("templates", []):
                    self.templates[t["id"]] = t
            logger.info(f"✅ Loaded {len(self.templates)} templates.")
        except Exception as e:
            logger.error(f"⚠️ Failed to load templates.json: {e}")

    async def _extract_image_context(self, image_path: str) -> str:
        """
        Feature 4: Vision Pre-processing
        Uses Gemini 2.5 Flash Vision to generate a rich, detailed textual description
        of the uploaded food image. This description is then fed into the DSPy pipeline
        to ensure the generated video matches the photo's visual characteristics.
        """
        if not image_path or not os.path.exists(image_path):
            return "No reference image provided. Generate a generic Korean restaurant food scene."

        logger.info(f"📸 Vision Pre-processing: Analyzing image → {image_path}")
        try:
            with open(image_path, "rb") as img_file:
                image_bytes = img_file.read()

            image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
            
            vision_prompt = """You are a professional food photographer analyzing a reference image for a video production.
Describe this food image in EXTREME DETAIL across these dimensions:
1. **Food Items**: What dishes are shown? Describe their exact colors, textures (glossy, matte, crispy, steaming), and arrangement.
2. **Plating & Presentation**: How is the food plated? (ceramic bowl, wooden board, fine china? garnish details?)
3. **Lighting**: What is the lighting style? (warm golden hour, cool daylight, overhead studio, candlelight, neon?)
4. **Color Palette**: List the dominant colors (e.g., rich amber broth, vibrant green garnish, pearl-white rice).
5. **Atmosphere**: What mood does the setting convey? (cozy home kitchen, upscale restaurant, street food stall, café?)
6. **Background/Environment**: Describe the table surface, background elements, and depth of field.

Be extremely specific. Your description will be used to generate a matching AI video."""

            pre_response = self.raw_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[vision_prompt, image_part]
            )
            
            image_description = pre_response.text
            logger.info(f"🔍 Vision Analysis Complete ({len(image_description)} chars)")
            logger.info(f"📝 Image Context Preview: {image_description[:200]}...")
            return image_description

        except Exception as img_err:
            logger.error(f"⚠️ Vision Pre-processing failed: {img_err}")
            return "Image analysis unavailable. Generate based on the concept description only."

    async def optimize_payload(self, payload: dict, image_path: str = None) -> dict:
        """
        Optimize the VeoPayload JSON using DSPy ChainOfThought with:
        - Feature 2: Camera Directing (lens, aperture, motion per vibe)
        - Feature 3: Negative Constraints (strict avoidance rules)
        - Feature 4: Vision Pre-processing (rich image description)
        """
        logger.info("🧠 DSPy Advanced Optimization Pipeline Starting...")

        try:
            # Extract key info for context
            metadata = payload.get("metadata", {})
            key_elements = payload.get("key_elements", [])
            
            concept_input = key_elements[0] if len(key_elements) > 0 else "Our signature Korean dish"
            persona_input = key_elements[1] if len(key_elements) > 1 else "A satisfied Korean customer"

            # Load vibe-specific template
            vibe_id = metadata.get("vibe_id", "energetic")
            selected_template = self.templates.get(vibe_id, self.templates.get("energetic", {}))
            
            # Feature 2: Camera Directing - extract professional camera metadata
            t_camera = selected_template.get("camera_setup", "Dynamic tracking shot, 24mm wide-angle lens")
            t_keywords = selected_template.get("visual_keywords", "Vibrant, Cinematic, High Definition")
            
            # Feature 3: Negative Constraints - extract strict avoidance rules
            t_negative = selected_template.get("negative_prompt", "blurry, distorted hands, messy eating")
            t_food_rule = selected_template.get("food_focus_rule", 
                "Focus on food texture and presentation over human eating actions. Show satisfied expressions after eating, not during.")

            # Feature 4: Vision Pre-processing - analyze the uploaded image
            image_context = await self._extract_image_context(image_path)

            # Map vibe_id to descriptive Korean label
            vibe_label_map = {
                "energetic": "에너지 (빠른 템포, 팝/역동적 스타일, 밝고 생동감 넘치는 분위기)",
                "luxury": "프리미엄 (차분하고 고급스러운 시네마틱 스타일, 파인다이닝 분위기)",
                "emotional": "무드 (잔잔하고 감성적인 인스타그램 스타일, 따뜻한 카페 분위기)"
            }
            target_vibe_label = vibe_label_map.get(vibe_id, "에너지")

            # DSPy ChainOfThought Optimization
            logger.info(f"🧠 DSPy ChainOfThought Triggered for vibe: {target_vibe_label}")
            logger.info(f"🎥 Camera Setup: {t_camera}")
            logger.info(f"🚫 Negative Constraints: {t_negative[:100]}...")
            logger.info(f"📐 Food Focus Rule: {t_food_rule[:100]}...")

            prediction = self.optimizer(
                target_persona=persona_input,
                concept=concept_input,
                target_vibe=target_vibe_label,
                camera_directing=t_camera,
                style_keywords=t_keywords,
                negative_constraints=t_negative,
                food_focus_rule=t_food_rule,
                image_visual_context=image_context
            )
            
            logger.info(f"💡 DSPy Rationale:\n{prediction.rationale}")
            
            # Parse Result
            try:
                # Clean up markdown code blocks if present
                clean_text = prediction.final_veo_json.replace("```json", "").replace("```", "").strip()
                optimized_json = json.loads(clean_text)
                logger.info("✨ DSPy JSON 파싱 성공")
                return optimized_json
            except json.JSONDecodeError as decode_err:
                logger.error(f"⚠️ Failed to parse DSPy output as JSON: {decode_err}\nRaw output: {prediction.final_veo_json}")
                return payload # Fallback

        except Exception as e:
            logger.error(f"⚠️ DSPy Optimization Failed: {str(e)}")
            return payload
