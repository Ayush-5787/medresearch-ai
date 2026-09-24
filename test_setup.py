"""
MedResearch AI — Setup Verification
Run this to verify everything is configured correctly.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def test_config():
    """Test 1: Config loads."""
    print("[1/4] Checking config...")
    try:
        from core.config import get_settings
        settings = get_settings()
        assert settings.groq_api_key, "GROQ_API_KEY missing"
        assert settings.tavily_api_key, "TAVILY_API_KEY missing"
        print("      OK - Config loaded")
        return True
    except Exception as e:
        print(f"      FAIL - {e}")
        return False


def test_llm():
    """Test 2: Groq LLM works."""
    print("[2/4] Testing Groq LLM...")
    try:
        from core.llm import get_llm
        llm = get_llm()
        response = llm.simple("Say 'Hello' and nothing else.", system="You are a test bot.")
        assert response, "Empty response"
        print(f"      OK - LLM replied: {response.strip()[:50]}")
        return True
    except Exception as e:
        print(f"      FAIL - {e}")
        return False


def test_web_search():
    """Test 3: Tavily search works."""
    print("[3/4] Testing Tavily web search...")
    try:
        from tools.web_search import get_web_search
        search = get_web_search()
        results = search.search("diabetes treatment", max_results=2)
        assert results, "No results returned"
        total_chars = sum(len(r["content"]) for r in results)
        print(f"      OK - Got {total_chars} chars of results")
        return True
    except Exception as e:
        print(f"      FAIL - {e}")
        return False


def test_scraper():
    """Test 4: URL scraper works."""
    print("[4/4] Testing URL scraper...")
    try:
        from tools.scrape_url import get_scraper
        scraper = get_scraper()
        text = scraper.scrape("https://example.com", max_chars=500)
        assert text, "No text scraped"
        print(f"      OK - Scraped {len(text)} chars")
        return True
    except Exception as e:
        print(f"      FAIL - {e}")
        return False


def main():
    print("=" * 60)
    print("TESTING SETUP")
    print("=" * 60)
    print()

    results = [
        test_config(),
        test_llm(),
        test_web_search(),
        test_scraper(),
    ]

    print()
    print("=" * 60)
    if all(results):
        print("ALL TESTS PASSED - READY FOR NEXT STEP")
        print("=" * 60)
        sys.exit(0)
    else:
        print(f"{results.count(False)} TEST(S) FAILED - FIX BEFORE PROCEEDING")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()