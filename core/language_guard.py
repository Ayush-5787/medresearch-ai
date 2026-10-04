"""
v1 language policy: English-only INPUT GUARD.

History (for the report): v0 attempted full multi-language support via
translate-then-retrieve. The evaluation harness showed non-English answers
could not be verified against English-language sources — verification of a
translation is not verification of a claim. v1 scopes input to English and
converts langdetect from a translator into a guard with a graceful,
distinctly-reasoned refusal path.

Known limitation (documented): Hinglish in Latin script (e.g. "kya metformin
ke side effects hain") may detect as English and pass the guard. Accepted
for v1; downstream verification gates remain the backstop.
"""

from langdetect import detect, DetectorFactory, LangDetectException

DetectorFactory.seed = 0  # detect() is non-deterministic without a fixed seed

SUPPORTED_LANGUAGE = "en"
REFUSAL_UNSUPPORTED_LANGUAGE = "unsupported_language"


def is_english(text: str) -> bool:
    if not text or len(text.strip()) < 3:
        return True
    try:
        return detect(text) == SUPPORTED_LANGUAGE
    except LangDetectException:
        return True


def language_guard(question: str):
    """Returns (ok, refusal_reason). ok=False → pipeline refuses in <1s, zero tokens."""
    if not is_english(question):
        return False, REFUSAL_UNSUPPORTED_LANGUAGE
    return True, None