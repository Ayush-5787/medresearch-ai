"""
MedResearch AI — Voice Handler
Handles speech-to-text (Whisper) and text-to-speech (gTTS).
"""

import io
from pathlib import Path
from typing import Optional
from groq import Groq
from core.config import get_settings


class VoiceHandler:
    """
    Handles voice input (transcription) and voice output (TTS).
    """

    def __init__(self):
        self.settings = get_settings()
        self.client = Groq(api_key=self.settings.groq_api_key)
        self.whisper_model = "whisper-large-v3"

    def transcribe(
        self,
        audio_bytes: bytes,
        language: Optional[str] = None,
    ) -> dict:
        """
        Transcribe audio to text using Groq Whisper.

        Args:
            audio_bytes: Raw audio file bytes (wav, mp3, m4a, webm, etc.)
            language: Optional ISO language code (e.g., 'hi', 'en')

        Returns:
            {"text": "...", "language": "hi"}
        """
        try:
            # Groq requires a file-like object with a name
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "audio.wav"

            kwargs = {
                "file": audio_file,
                "model": self.whisper_model,
                "response_format": "json",
            }
            if language and language != "auto":
                kwargs["language"] = language

            response = self.client.audio.transcriptions.create(**kwargs)
            return {
                "text": response.text.strip(),
                "language": getattr(response, "language", language or "auto"),
            }
        except Exception as e:
            print(f"[VoiceHandler] Transcription error: {e}")
            return {"text": "", "language": "unknown", "error": str(e)}

    def synthesize(
        self,
        text: str,
        language: str = "en",
    ) -> Optional[bytes]:
        """
        Convert text to speech using gTTS.

        Args:
            text: Text to speak
            language: ISO language code (e.g., 'en', 'hi')

        Returns:
            MP3 audio bytes, or None on failure
        """
        try:
            from gtts import gTTS

            # Map ISO codes to gTTS language codes
            lang_map = {
                "zh-cn": "zh-CN",
                "zh-tw": "zh-TW",
                "en": "en",
                "hi": "hi",
                "es": "es",
                "fr": "fr",
                "de": "de",
                "ja": "ja",
                "ko": "ko",
                "ar": "ar",
                "pt": "pt",
                "ru": "ru",
                "it": "it",
                "ta": "ta",
                "te": "te",
                "bn": "bn",
                "mr": "mr",
                "gu": "gu",
                "kn": "kn",
                "ml": "ml",
                "pa": "pa",
                "ur": "ur",
                "ne": "ne",
                "si": "si",
                "tr": "tr",
                "vi": "vi",
                "th": "th",
                "id": "id",
                "ms": "ms",
                "tl": "tl",
                "sw": "sw",
                "af": "af",
                "nl": "nl",
                "pl": "pl",
                "sv": "sv",
                "da": "da",
                "fi": "fi",
                "no": "no",
                "el": "el",
                "cs": "cs",
                "hu": "hu",
                "ro": "ro",
                "uk": "uk",
                "bg": "bg",
                "he": "iw",
                "fa": "fa",
            }

            gtts_lang = lang_map.get(language, "en")

            # Truncate very long text (gTTS has limits)
            if len(text) > 5000:
                text = text[:5000]

            tts = gTTS(text=text, lang=gtts_lang, slow=False)
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            return audio_buffer.read()
        except Exception as e:
            print(f"[VoiceHandler] TTS error: {e}")
            return None

    def list_available_languages(self) -> list:
        """Return list of languages with TTS support."""
        return [
            "en", "hi", "es", "fr", "de", "it", "pt", "ru", "ja", "ko",
            "ar", "zh-cn", "ta", "te", "bn", "mr", "gu", "kn", "ml", "pa",
            "ur", "ne", "si", "tr", "vi", "th", "id", "ms", "tl", "sw",
        ]


print("[voice] VoiceHandler loaded")