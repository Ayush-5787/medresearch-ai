"""
MedResearch AI — Image Reader
Extracts text from medical images (prescriptions, medicine boxes, reports) using OCR.
"""

import io
from pathlib import Path
from typing import Optional, Dict

import pytesseract
from PIL import Image


# ============================================================
# CONFIGURE TESSERACT PATH
# ============================================================

# Windows default path
TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Users\hp\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
    "/usr/bin/tesseract",  # Linux
    "/usr/local/bin/tesseract",  # Mac
]

for path in TESSERACT_PATHS:
    if Path(path).exists():
        pytesseract.pytesseract.tesseract_cmd = path
        break


class ImageReader:
    """
    Reads text from images using Tesseract OCR.
    Supports prescriptions, medicine boxes, reports.
    """

    # Languages supported by Tesseract (must match installed language packs)
    SUPPORTED_LANGS = {
        "eng": "English",
        "hin": "Hindi",
        "tam": "Tamil",
        "tel": "Telugu",
        "ben": "Bengali",
        "mar": "Marathi",
        "guj": "Gujarati",
        "kan": "Kannada",
        "mal": "Malayalam",
        "pan": "Punjabi",
        "urd": "Urdu",
        "spa": "Spanish",
        "fra": "French",
        "deu": "German",
        "ara": "Arabic",
        "chi_sim": "Chinese (Simplified)",
        "jpn": "Japanese",
        "kor": "Korean",
        "rus": "Russian",
        "por": "Portuguese",
    }

    def __init__(self, lang: str = "eng"):
        """
        Initialize reader.

        Args:
            lang: Tesseract language code (eng, hin, tam, etc.)
                  Use '+' for multiple: 'eng+hin'
        """
        self.lang = lang

    def extract_text(
        self,
        image_bytes: bytes,
        lang: Optional[str] = None,
    ) -> Dict:
        """
        Extract text from image.

        Args:
            image_bytes: Raw image bytes (jpg, png, etc.)
            lang: Override language for this call

        Returns:
            {
                "text": "extracted text",
                "confidence": 0.0-1.0,
                "word_count": N,
                "error": None or "error message"
            }
        """
        try:
            # Load image from bytes
            image = Image.open(io.BytesIO(image_bytes))

            # Convert to RGB if needed
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Run OCR
            use_lang = lang or self.lang
            text = pytesseract.image_to_string(image, lang=use_lang)

            # Clean text
            text = text.strip()
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            clean_text = " ".join(lines)

            # Get confidence
            data = pytesseract.image_to_data(
                image, lang=use_lang, output_type=pytesseract.Output.DICT
            )
            confidences = [int(c) for c in data["conf"] if int(c) > 0]
            avg_conf = sum(confidences) / len(confidences) / 100 if confidences else 0.0

            return {
                "text": clean_text,
                "confidence": round(avg_conf, 2),
                "word_count": len(clean_text.split()),
                "error": None,
            }
        except Exception as e:
            return {
                "text": "",
                "confidence": 0.0,
                "word_count": 0,
                "error": str(e),
            }

    def extract_with_multilang(
        self,
        image_bytes: bytes,
        languages: list = None,
    ) -> Dict:
        """
        Extract text using multiple languages.

        Args:
            image_bytes: Image bytes
            languages: List of language codes like ['eng', 'hin']

        Returns:
            Same dict as extract_text
        """
        if not languages:
            languages = ["eng"]

        lang_string = "+".join(languages)
        return self.extract_text(image_bytes, lang=lang_string)

    def is_available(self) -> bool:
        """Check if Tesseract is available."""
        try:
            version = pytesseract.get_tesseract_version()
            return version is not None
        except Exception:
            return False

    def get_version(self) -> str:
        """Get Tesseract version."""
        try:
            return str(pytesseract.get_tesseract_version())
        except Exception:
            return "not available"


print("[image_reader] ImageReader loaded")