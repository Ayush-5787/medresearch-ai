"""
MedResearch AI — Test Multi-Language Support
Tests language detection, translation, and country configuration.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.language import LanguageHandler
from core.country import CountryConfig


def main():
    print("=" * 60)
    print("TESTING LANGUAGE + COUNTRY SUPPORT")
    print("=" * 60)

    lang = LanguageHandler()
    country = CountryConfig()

    # ==========================================================
    # TEST 1: Language Detection
    # ==========================================================
    print("\nTEST 1: Language Detection")
    print("-" * 60)

    test_cases = [
        ("What are the side effects of metformin?", "en"),
        ("मेटफॉर्मिन के दुष्प्रभाव क्या हैं?", "hi"),
        ("¿Cuáles son los efectos secundarios de la metformina?", "es"),
        ("Quels sont les effets secondaires de la metformine?", "fr"),
        ("ما هي الآثار الجانبية للميتفورمين؟", "ar"),
        ("メトホルミンの副作用は何ですか？", "ja"),
        ("मेटफॉर्मिनचे दुष्परिणाम काय आहेत?", "mr"),
        ("மெட்ஃபார்மினின் பக்க விளைவுகள் என்ன?", "ta"),
        ("মেটফর্মিনের পার্শ্বপ্রতিক্রিয়া কি?", "bn"),
        ("메트포르민의 부작용은 무엇입니까?", "ko"),
        ("Quais são os efeitos colaterais da metformina?", "pt"),
        ("Was sind die Nebenwirkungen von Metformin?", "de"),
    ]

    for text, expected in test_cases:
        detected = lang.detect_language(text)
        icon = "OK " if detected == expected else "!! "
        print(f"{icon} '{text[:45]}...' -> detected: {detected} (expected: {expected})")

    # ==========================================================
    # TEST 2: Translation
    # ==========================================================
    print("\nTEST 2: Translation")
    print("-" * 60)

    hindi_q = "मेटफॉर्मिन के दुष्प्रभाव क्या हैं?"
    print(f"\nOriginal (Hindi): {hindi_q}")

    english = lang.translate_to_english(hindi_q, "hi")
    print(f"Translated (English): {english}")

    back_to_hindi = lang.translate_from_english(english, "hi")
    print(f"Back to Hindi: {back_to_hindi}")

    # ==========================================================
    # TEST 3: Citation Preservation
    # ==========================================================
    print("\nTEST 3: Citation Preservation in Translation")
    print("-" * 60)

    test_answer = "Metformin causes nausea [1]. Lactic acidosis is rare [2]."
    print(f"\nOriginal: {test_answer}")

    for lang_code in ["hi", "es", "fr"]:
        translated = lang.translate_from_english(test_answer, lang_code)
        has_citations = "[1]" in translated and "[2]" in translated
        icon = "OK " if has_citations else "!! "
        print(f"\n{icon} {lang.get_language_name(lang_code)}:")
        print(f"   {translated[:120]}...")

    # ==========================================================
    # TEST 4: Country Configuration
    # ==========================================================
    print("\n\nTEST 4: Country Configuration")
    print("-" * 60)

    countries = country.list_countries()
    print(f"\nSupported countries: {len(countries)}")
    for c in countries[:5]:
        print(f"  - {c['name']} ({c['code']}): {', '.join(c['languages'])}")

    # Emergency numbers
    print("\nEmergency numbers:")
    for code in ["IN", "US", "GB", "AU", "DEFAULT"]:
        info = country.get(code)
        print(f"  - {info.get('name')}: {info.get('emergency')}")

    # Trusted sources
    print("\nIndia trusted sources:")
    for s in country.get_trusted_sources("IN"):
        print(f"  - {s['name']}: {s['url']}")

    # ==========================================================
    # TEST 5: Supported Languages
    # ==========================================================
    print("\n\nTEST 5: Supported Languages")
    print("-" * 60)

    langs = lang.list_languages()
    print(f"\nTotal supported: {len(langs)}")
    for code, name in list(langs.items())[:10]:
        print(f"  - {code}: {name}")
    print(f"  ... and {len(langs) - 10} more")

    print("\n" + "=" * 60)
    print("LANGUAGE TESTS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()