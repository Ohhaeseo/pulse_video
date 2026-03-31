"""
tts_service.py
Google Cloud Text-to-Speech API를 호출하여, 
광고 영상에 들어갈 짧은 내레이션(오디오 스크립트)을 mp3 파일로 합성하는 서비스입니다.
"""
import os
import logging
from google.cloud import texttospeech

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self):
        # Requires GOOGLE_APPLICATION_CREDENTIALS or ADC to be configured properly
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        try:
            self.client = texttospeech.TextToSpeechClient()
            logger.info("✅ Google Cloud TTS Client initialized.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize TTS Client: {e}")
            self.client = None

    async def generate_speech(self, text: str, output_path: str, voice_name: str = "ko-KR-Neural2-A") -> str:
        """
        Generate Korean TTS audio and save to output_path.
        Returns the output_path if successful, None otherwise.
        """
        if not self.client:
            logger.warning("⚠️ TTS Client not available. Skipping audio generation.")
            return None

        if not text or not text.strip():
            logger.warning("⚠️ Empty text provided. Skipping audio generation.")
            return None

        try:
            synthesis_input = texttospeech.SynthesisInput(text=text)

            # Build the voice request
            voice = texttospeech.VoiceSelectionParams(
                language_code="ko-KR",
                name=voice_name
            )

            # Select the type of audio file you want returned
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )

            # Perform the text-to-speech request
            response = self.client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )

            # Make sure the directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with open(output_path, "wb") as out:
                out.write(response.audio_content)
                logger.info(f"🎤 Audio content written to file: {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"❌ TTS Generation Failed: {str(e)}")
            return None
