"""
MedResearch AI — Language Handler (Full Multi-Language)
Detects any language and translates via LLM.
Supports 100+ languages.
"""

from typing import Tuple, Optional, List, Dict
from core.llm import get_llm


class LanguageHandler:
    """
    Handles language detection and translation for ANY language.
    Uses langdetect for detection and Groq LLM for translation.
    """

    # All languages the LLM can handle (100+)
    SUPPORTED = {
        # Indian Languages
        "en": "English",
        "hi": "Hindi",
        "ta": "Tamil",
        "te": "Telugu",
        "bn": "Bengali",
        "mr": "Marathi",
        "gu": "Gujarati",
        "kn": "Kannada",
        "ml": "Malayalam",
        "pa": "Punjabi",
        "ur": "Urdu",
        "or": "Odia",
        "as": "Assamese",
        "ne": "Nepali",
        "si": "Sinhala",
        # Asian Languages
        "zh-cn": "Chinese (Simplified)",
        "zh-tw": "Chinese (Traditional)",
        "ja": "Japanese",
        "ko": "Korean",
        "vi": "Vietnamese",
        "th": "Thai",
        "id": "Indonesian",
        "ms": "Malay",
        "tl": "Filipino",
        "my": "Burmese",
        "km": "Khmer",
        # European Languages
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "ru": "Russian",
        "nl": "Dutch",
        "pl": "Polish",
        "sv": "Swedish",
        "no": "Norwegian",
        "da": "Danish",
        "fi": "Finnish",
        "el": "Greek",
        "cs": "Czech",
        "hu": "Hungarian",
        "ro": "Romanian",
        "uk": "Ukrainian",
        "bg": "Bulgarian",
        "hr": "Croatian",
        "sr": "Serbian",
        "sk": "Slovak",
        "sl": "Slovenian",
        "lt": "Lithuanian",
        "lv": "Latvian",
        "et": "Estonian",
        "is": "Icelandic",
        "ga": "Irish",
        "cy": "Welsh",
        "ca": "Catalan",
        "eu": "Basque",
        "gl": "Galician",
        # Middle Eastern Languages
        "ar": "Arabic",
        "he": "Hebrew",
        "fa": "Persian",
        "tr": "Turkish",
        "ku": "Kurdish",
        # African Languages
        "sw": "Swahili",
        "am": "Amharic",
        "yo": "Yoruba",
        "zu": "Zulu",
        "af": "Afrikaans",
        "ha": "Hausa",
        "so": "Somali",
        # Others
        "la": "Latin",
        "eo": "Esperanto",
    }

    def __init__(self):
        self.llm = get_llm()
        # Try to import langdetect
        try:
            from langdetect import detect, DetectorFactory
            DetectorFactory.seed = 0  # Deterministic
            self._langdetect = detect
            self._has_langdetect = True
            print("[LanguageHandler] langdetect loaded")
        except ImportError:
            self._langdetect = None
            self._has_langdetect = False
            print("[LanguageHandler] langdetect NOT installed — will use character-based detection")

    def detect_language(self, text: str) -> str:
        """
        Detect the language of input text.
        Uses langdetect first, then character-based fallback.
        Returns ISO 639-1 code like 'en', 'hi', 'zh-cn', etc.
        """
        if not text or len(text.strip()) < 3:
            return "en"

        # Try langdetect first (100+ languages)
        if self._has_langdetect:
            try:
                detected = self._langdetect(text)
                # Normalize
                if detected.startswith("zh"):
                    # Handle Chinese variants
                    if any("\u4E00" <= c <= "\u9FFF" for c in text):
                        return "zh-cn"
                return detected
            except Exception:
                pass

        # Fallback: character-based detection
        return self._char_based_detection(text)

    def _char_based_detection(self, text: str) -> str:
        """Character-based detection for common scripts."""
        scripts = [
            ("\u0900", "\u097F", "hi"),     # Devanagari
            ("\u0B80", "\u0BFF", "ta"),     # Tamil
            ("\u0980", "\u09FF", "bn"),     # Bengali
            ("\u0C00", "\u0C7F", "te"),     # Telugu
            ("\u0A80", "\u0AFF", "gu"),     # Gujarati
            ("\u0C80", "\u0CFF", "kn"),     # Kannada
            ("\u0D00", "\u0D7F", "ml"),     # Malayalam
            ("\u0A00", "\u0A7F", "pa"),     # Punjabi
            ("\u0600", "\u06FF", "ar"),     # Arabic
            ("\u05D0", "\u05EA", "he"),     # Hebrew
            ("\u4E00", "\u9FFF", "zh-cn"),  # Chinese
            ("\u3040", "\u309F", "ja"),     # Hiragana
            ("\u30A0", "\u30FF", "ja"),     # Katakana
            ("\uAC00", "\uD7AF", "ko"),     # Korean
            ("\u0E00", "\u0E7F", "th"),     # Thai
            ("\u0400", "\u04FF", "ru"),     # Cyrillic
            ("\u0590", "\u05FF", "he"),     # Hebrew
            ("\u0D80", "\u0DFF", "si"),     # Sinhala
            ("\u0E80", "\u0EFF", "lo"),     # Lao
        ]

        threshold = max(2, len(text) * 0.15)
        counts = {}
        for start, end, code in scripts:
            count = sum(1 for c in text if start <= c <= end)
            if count > threshold:
                counts[code] = counts.get(code, 0) + count

        if counts:
            return max(counts, key=counts.get)
        return "en"

    def translate_to_english(self, text: str, source_lang: str) -> str:
        """Translate text from any language to English."""
        if source_lang == "en":
            return text

        lang_name = self.SUPPORTED.get(source_lang, source_lang)

        prompt = f"""Translate the following medical question from {lang_name} to English.

RULES:
1. Preserve medical terms accurately (translate to standard English medical terminology).
2. Keep the meaning exact.
3. Return ONLY the translation — no explanations, no quotes, no markdown.

Text:
{text}

English translation:"""

        try:
            response = self.llm.simple(
                prompt,
                system="You are a medical translator. Return only the translated text.",
            )
            return response.strip()
        except Exception as e:
            print(f"[LanguageHandler] Translation error: {e}")
            return text

    def translate_from_english(self, text: str, target_lang: str) -> str:
        """Translate English text to any target language."""
        if target_lang == "en":
            return text

        lang_name = self.SUPPORTED.get(target_lang, target_lang)

        prompt = f"""Translate the following medical answer from English to {lang_name}.

CRITICAL RULES:
1. PRESERVE all citation numbers exactly: [1], [2], [3] etc. — do NOT change them.
2. Keep medical terms accurate. Where helpful, include the English term in parentheses.
3. Maintain the disclaimer at the end (translate it).
4. Keep the same structure (paragraphs, line breaks).
5. Return ONLY the translation — no explanations.

Text:
{text}

{lang_name} translation:"""

        try:
            response = self.llm.simple(
                prompt,
                system="You are a medical translator. Preserve [N] citations exactly.",
            )
            return response.strip()
        except Exception as e:
            print(f"[LanguageHandler] Translation error: {e}")
            return text

    def get_language_name(self, code: str) -> str:
        """Get full language name from code."""
        return self.SUPPORTED.get(code, code)

    def list_languages(self) -> Dict[str, str]:
        """List all supported languages."""
        return self.SUPPORTED.copy()

    def count_languages(self) -> int:
        """Count supported languages."""
        return len(self.SUPPORTED)


print("[language] LanguageHandler loaded (full multi-language)")