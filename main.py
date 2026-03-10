from fastapi import FastAPI, Form, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
# from services.veo_service import VeoService # [DISABLED]
from services.veo_service import VeoService # [DISABLED]
# from services.luma_service import LumaService # [DISABLED]
from services.vertex_video_service import VertexVideoService # [ENABLED]
from pydantic import BaseModel
from typing import List, Optional
import json
import shutil
import os

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
# ...
# veo_service = VeoService()
# luma_service = LumaService()
vertex_video_service = VertexVideoService()

# 프론트엔드 정적 파일 연결
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Pydantic Models for Validation ---
class VeoMetadata(BaseModel):
    prompt_name: str
    base_style: str
    aspect_ratio: str
    duration: str
    location: str
    camera_setup: str
    vibe_id: str = "energetic" # [ADDED] Default value

class TimelineItem(BaseModel):
    sequence: int
    section: str
    timestamp: str
    action: str
    audio: str

class VeoPayload(BaseModel):
    metadata: VeoMetadata
    key_elements: List[str]
    negative_prompts: List[str]
    timeline: List[TimelineItem]

@app.post("/api/generate")
async def generate_endpoint(
    payload: str = Form(...), # JSON string
    image: Optional[UploadFile] = File(None)
):
    try:
        # 1. Parse JSON Payload
        try:
            payload_dict = json.loads(payload)
            # Validate with Pydantic (Optional but good for safety)
            # veo_data = VeoPayload(**payload_dict) 
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")

        print(f"📩 [API 요청] Payload 수신 (Vertex AI 연결)")
        
        # 2. Handle Image Upload
        image_path = None
        if image:
            os.makedirs("static/uploads", exist_ok=True)
            image_path = f"static/uploads/{image.filename}"
            with open(image_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)
            print(f"🖼️ [이미지 업로드] 저장 경로: {image_path}")

        # 3. Call Luma Service (Previously Vertex/Veo)
        # video_url = await veo_service.generate_video(payload_dict, image_path)
        # video_url = await luma_service.generate_video(payload_dict, image_path)
        video_url = await vertex_video_service.generate_video(payload_dict, image_path)
        
        return {"status": "success", "video_url": video_url}

    except Exception as e:
        print(f"❌ [Server Error] {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Promotion API (New) ---
from services.llm_service import LLMService

llm_service = LLMService()

@app.post("/api/info/generate")
async def generate_promotion_video(
    target: str = Form(...),
    concept: str = Form(...),
    mode: str = Form(...),
    style: str = Form(...),
    image: UploadFile = File(...)
):
    try:
        print(f"🎬 [Promotion API] 요청 수신: 타겟={target}, 컨셉={concept}, 스타일={style}")

        # 1. 이미지 저장
        os.makedirs("static/uploads", exist_ok=True)
        image_path = f"static/uploads/{image.filename}"
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        # 2. LLM을 사용하여 영상 생성용 Payload 생성 (Prompt Engineering)
        raw_context = {
            "metadata": {
                "vibe_id": style, # energy, premium, mood
                "base_style": f"Targeting {target}"
            },
            "key_elements": [
                f"Concept: {concept}",
                f"Target: {target}",
                "No text", "Cinematic food shot"
            ],
            "timeline": [] # LLM이 채워줄 부분
        }

        # LLM 호출 -> 최적화된 Veo Payload (Title, Hashtags 포함)
        optimized_payload = await llm_service.optimize_payload(raw_context, image_path)
        
        # 3. 영상 생성 요청 (Vertex AI)
        # VertexVideoService는 metadata, timeline 등을 사용
        video_url = await vertex_video_service.generate_video(optimized_payload, image_path)
        # video_url = await luma_service.generate_video(optimized_payload, image_path)

        # 4. 메타데이터 추출
        video_title = optimized_payload.get("title", f"{target}을 위한 {concept}")
        hashtags = optimized_payload.get("hashtags", ["#맛집", "#추천"])

        return {
            "status": "success", 
            "video_url": video_url,
            "video_title": video_title,
            "hashtags": hashtags
        }

    except Exception as e:
        print(f"❌ [Promotion API Error] {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # 서버 실행
    uvicorn.run(app, host="0.0.0.0", port=8000)