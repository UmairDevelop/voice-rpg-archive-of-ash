import os
import asyncio
import logging
from typing import Optional, Tuple
import edge_tts
import httpx

from .cleanup import clean_text_for_speech

logger = logging.getLogger("TTSVoiceEngine")


class TTSVoiceEngine:
    """
    Streaming Text-To-Speech engine with ElevenLabs support and Edge-TTS fallback.
    Applies pure-function text cleanup before passing text to audio synthesis.
    """
    def __init__(
        self,
        elevenlabs_api_key: Optional[str] = None,
        voice_id: str = "21m00Tcm4TlvDq8ikWAM",  # ElevenLabs Rachel voice
        edge_voice: str = "en-US-SteffanNeural", # Edge-TTS robot/monotone voice for Archivist
    ):
        self.api_key = elevenlabs_api_key or os.environ.get("ELEVENLABS_API_KEY", "")
        self.voice_id = voice_id
        self.edge_voice = edge_voice

    async def generate_speech_audio(self, text: str, output_path: Optional[str] = None) -> Tuple[bool, str, str]:
        """
        Cleans text and generates audio file.
        Returns (success, cleaned_text, file_path_or_error)
        """
        cleaned_text = clean_text_for_speech(text)
        if not cleaned_text or len(cleaned_text.strip()) == 0:
            return False, "", "Empty cleaned text."

        if not output_path:
            import time
            output_path = f"temp_speech_{time.time_ns()}.mp3"

        # Attempt stale file cleanup
        try:
            for fname in os.listdir("."):
                if fname.startswith("temp_speech_") and fname.endswith(".mp3") and fname != output_path:
                    try:
                        os.remove(fname)
                    except OSError:
                        pass
        except Exception:
            pass

        # 1. Try ElevenLabs streaming if API key present
        if self.api_key:
            try:
                url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
                headers = {
                    "Accept": "audio/mpeg",
                    "Content-Type": "application/json",
                    "xi-api-key": self.api_key,
                }
                data = {
                    "text": cleaned_text,
                    "model_id": "eleven_flash_v3",
                    "voice_settings": {"stability": 0.5, "similarity_boost": 0.8},
                }
                async with httpx.AsyncClient() as client:
                    resp = await client.post(url, json=data, headers=headers, timeout=10.0)
                    if resp.status_code == 200:
                        with open(output_path, "wb") as f:
                            f.write(resp.content)
                        return True, cleaned_text, output_path
            except Exception as e:
                logger.warning(f"ElevenLabs TTS failed: {e}. Falling back to Edge-TTS.")

        # 2. Fallback to Edge-TTS (Free Neural TTS)
        try:
            communicate = edge_tts.Communicate(cleaned_text, self.edge_voice)
            await communicate.save(output_path)
            return True, cleaned_text, output_path
        except Exception as e:
            logger.error(f"Edge-TTS failed: {e}. Returning speech text without audio.")
            return False, cleaned_text, f"TTS error: {str(e)}"
