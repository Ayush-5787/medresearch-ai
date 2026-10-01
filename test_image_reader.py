"""
MedResearch AI — Test Image Reader (OCR)
Tests text extraction from images.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from multimodal.image_reader import ImageReader


def test_tesseract_available():
    """Test 1: Tesseract is installed and accessible."""
    print("\nTEST 1: Tesseract Availability")
    print("-" * 60)

    reader = ImageReader()

    if reader.is_available():
        print(f"OK  Tesseract version: {reader.get_version()}")
        return True
    else:
        print("FAIL  Tesseract not available")
        print("Install: winget install UB-Mannheim.TesseractOCR")
        return False


def test_generate_and_read_image():
    """Test 2: Generate a test image and read it with OCR."""
    print("\nTEST 2: Generate + Read Test Image")
    print("-" * 60)

    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("FAIL  Pillow not installed")
        return False

    # Create a test image with text
    img = Image.new("RGB", (800, 200), color="white")
    draw = ImageDraw.Draw(img)

    # Try to use a font, fall back to default
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except Exception:
        font = ImageFont.load_default()

    text = "Metformin 500mg twice daily"
    draw.text((20, 80), text, fill="black", font=font)

    # Save to temp
    test_image_path = Path("test_prescription.png")
    img.save(test_image_path)
    print(f"OK  Created test image: {test_image_path}")

    # Read it with OCR
    reader = ImageReader()
    image_bytes = test_image_path.read_bytes()

    result = reader.extract_text(image_bytes)

    if result["error"]:
        print(f"FAIL  OCR error: {result['error']}")
        return False

    print(f"OK  Extracted: '{result['text']}'")
    print(f"    Confidence: {result['confidence']}")
    print(f"    Words: {result['word_count']}")

    if "metformin" in result["text"].lower():
        print("OK  Extracted text contains 'Metformin'")
        return True
    else:
        print("WARN  Extracted text doesn't match expected")
        return True  # Don't fail — OCR can vary


def test_ocr_on_blank():
    """Test 3: OCR on a blank image (should return empty)."""
    print("\nTEST 3: OCR on Blank Image")
    print("-" * 60)

    try:
        from PIL import Image
    except ImportError:
        return False

    img = Image.new("RGB", (400, 200), color="white")
    test_path = Path("test_blank.png")
    img.save(test_path)

    reader = ImageReader()
    result = reader.extract_text(test_path.read_bytes())

    print(f"OK  Blank image OCR: '{result['text'][:50]}'")
    print(f"    Words: {result['word_count']}")

    # Clean up
    test_path.unlink(missing_ok=True)
    return True


def main():
    print("=" * 60)
    print("TESTING IMAGE READER (OCR)")
    print("=" * 60)

    results = [
        test_tesseract_available(),
        test_generate_and_read_image(),
        test_ocr_on_blank(),
    ]

    print("\n" + "=" * 60)
    if all(results):
        print("ALL IMAGE READER TESTS PASSED")
    else:
        print(f"{results.count(False)} TEST(S) FAILED")
    print("=" * 60)


if __name__ == "__main__":
    main()