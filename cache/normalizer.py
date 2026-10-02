"""
MedResearch AI — Question normalization for cache keys.
Ensures "What ARE side effects?" and "what are side effects" hit same cache.
"""

import re
import hashlib


# Common stop words to strip (optional)
STOP_WORDS = {
    "what", "are", "is", "the", "a", "an", "of", "for", "to",
    "do", "does", "did", "can", "could", "would", "should",
    "tell", "me", "about", "please", "how",
}


def normalize_question(question: str) -> str:
    """
    Normalize a question for cache key generation.
    - Lowercase
    - Strip extra whitespace
    - Remove punctuation
    - Remove emojis
    """
    if not question:
        return ""

    # Lowercase
    q = question.lower()

    # Remove emojis (unicode ranges)
    q = re.sub(r"[\U0001F300-\U0001F9FF]", "", q)

    # Remove punctuation except spaces
    q = re.sub(r"[^\w\s]", " ", q)

    # Collapse whitespace
    q = re.sub(r"\s+", " ", q).strip()

    return q


def generate_cache_key(question: str, language: str, country: str) -> str:
    """
    Generate a SHA256 hash from normalized question + language + country.
    Different language or country → different cache key.
    """
    normalized = normalize_question(question)
    raw_key = f"{normalized}|{language}|{country}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()