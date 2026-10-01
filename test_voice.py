"""
MedResearch AI — Test Voice Handler
Tests text-to-speech synthesis (voice output).
Note: Voice input needs an actual audio file to test.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.voice import VoiceHandler


def main():
    print("=" * 60)
    print("TESTING VOICE HANDLER")
    print("=" * 60)

    voice = VoiceHandler()

    # ==========================================================
    # TEST 1: Text-to-Speech (English)
    # ==========================================================
    print("\nTEST 1: Text-to-Speech (English)")
    print("-" * 60)

    text_en = "Metformin causes nausea and diarrhea. Consult a licensed doctor."
    audio_en = voice.synthesize(text_en, "en")

    if audio_en:
        output_path = Path("test_voice_en.mp3")
        output_path.write_bytes(audio_en)
        print(f"OK  Generated {len(audio_en)} bytes of audio")
        print(f"    Saved to: {output_path.absolute()}")
        print(f"    Play it with: start {output_path.name}")
    else:
        print("FAIL  Could not generate audio")

    # ==========================================================
    # TEST 2: Text-to-Speech (Hindi)
    # ==========================================================
    print("\nTEST 2: Text-to-Speech (Hindi)")
    print("-" * 60)

    text_hi = "मेटफॉर्मिन से मतली और दस्त हो सकते हैं। कृपया डॉक्टर से सलाह लें।"
    audio_hi = voice.synthesize(text_hi, "hi")

    if audio_hi:
        output_path = Path("test_voice_hi.mp3")
        output_path.write_bytes(audio_hi)
        print(f"OK  Generated {len(audio_hi)} bytes of audio")
        print(f"    Saved to: {output_path.absolute()}")
        print(f"    Play it with: start {output_path.name}")
    else:
        print("FAIL  Could not generate audio")

    # ==========================================================
    # TEST 3: Text-to-Speech (Spanish)
    # ==========================================================
    print("\nTEST 3: Text-to-Speech (Spanish)")
    print("-" * 60)

    text_es = "La metformina causa náuseas. Consulte a un médico."
    audio_es = voice.synthesize(text_es, "es")

    if audio_es:
        output_path = Path("test_voice_es.mp3")
        output_path.write_bytes(audio_es)
        print(f"OK  Generated {len(audio_es)} bytes of audio")
        print(f"    Saved to: {output_path.absolute()}")
    else:
        print("FAIL  Could not generate audio")

    # ==========================================================
    # TEST 4: List supported languages
    # ==========================================================
    print("\nTEST 4: TTS-Supported Languages")
    print("-" * 60)
    langs = voice.list_available_languages()
    print(f"Total: {len(langs)}")
    print(f"Languages: {', '.join(langs)}")

    # ==========================================================
    # Summary
    # ==========================================================
    print("\n" + "=" * 60)
    print("VOICE TESTS COMPLETE")
    print("=" * 60)
    print("\nTo play generated audio, run:")
    print("  start test_voice_en.mp3")
    print("  start test_voice_hi.mp3")
    print("  start test_voice_es.mp3")


if __name__ == "__main__":
    main()