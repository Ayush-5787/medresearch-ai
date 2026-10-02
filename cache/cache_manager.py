"""
MedResearch AI — Cache manager (SQLite).
Stores and retrieves cached answers to save LLM tokens.

IMPORTANT: Only caches SUCCESSFUL answers. Refusals, low-confidence results,
and empty answers are never cached because they usually come from temporary
issues like rate limits or missing sources.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

from cache.normalizer import generate_cache_key, normalize_question


DB_PATH = Path(__file__).parent.parent / "response_cache.db"
DEFAULT_TTL_DAYS = 30
MAX_CACHE_ENTRIES = 1000

# Minimum thresholds for caching
MIN_CONFIDENCE_TO_CACHE = 0.3
MIN_ANSWER_LENGTH_TO_CACHE = 200


class CacheManager:
    """SQLite-backed response cache."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS response_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cache_key TEXT UNIQUE NOT NULL,
                question TEXT NOT NULL,
                normalized_question TEXT NOT NULL,
                language TEXT NOT NULL,
                country TEXT NOT NULL,
                answer TEXT NOT NULL,
                sources_json TEXT,
                claims_json TEXT,
                verification_json TEXT,
                confidence REAL,
                decision TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                hit_count INTEGER DEFAULT 0
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cache_key ON response_cache(cache_key)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_last_used ON response_cache(last_used_at)")
        conn.commit()
        conn.close()

    def get(self, question: str, language: str, country: str) -> Optional[Dict[str, Any]]:
        """
        Look up a cached answer.
        Returns dict with keys: question, answer, sources, claims, verification,
        confidence, decision, hit_count, cached_at.
        Or None if not found / expired / REFUSED / low-quality.
        """
        key = generate_cache_key(question, language, country)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT question, answer, sources_json, claims_json, verification_json,
                   confidence, decision, hit_count, created_at
            FROM response_cache
            WHERE cache_key = ?
        """, (key,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return None

        # ─────────────────────────────────────────────────────────
        # SAFETY CHECK 1: Never serve a REFUSED entry from cache.
        # ─────────────────────────────────────────────────────────
        if row[6] == "REFUSED":
            cursor.execute("DELETE FROM response_cache WHERE cache_key = ?", (key,))
            conn.commit()
            conn.close()
            return None

        # ─────────────────────────────────────────────────────────
        # SAFETY CHECK 2: Never serve a low-confidence or empty answer.
        # ─────────────────────────────────────────────────────────
        if (row[5] is None or row[5] < MIN_CONFIDENCE_TO_CACHE) or (not row[1] or len(row[1]) < MIN_ANSWER_LENGTH_TO_CACHE):
            cursor.execute("DELETE FROM response_cache WHERE cache_key = ?", (key,))
            conn.commit()
            conn.close()
            return None

        # Check expiry
        created_at = datetime.fromisoformat(row[8])
        if datetime.now() - created_at > timedelta(days=DEFAULT_TTL_DAYS):
            # Expired — delete
            cursor.execute("DELETE FROM response_cache WHERE cache_key = ?", (key,))
            conn.commit()
            conn.close()
            return None

        # Update last_used + hit_count
        cursor.execute("""
            UPDATE response_cache
            SET last_used_at = ?, hit_count = hit_count + 1
            WHERE cache_key = ?
        """, (datetime.now().isoformat(), key))
        conn.commit()
        conn.close()

        return {
            "question": row[0],
            "answer": row[1],
            "sources": json.loads(row[2]) if row[2] else [],
            "claims": json.loads(row[3]) if row[3] else [],
            "verification": json.loads(row[4]) if row[4] else {},
            "confidence": row[5],
            "decision": row[6],
            "hit_count": row[7] + 1,
            "cached_at": row[8],
        }

    def set(self, question: str, language: str, country: str, result: Any) -> bool:
        """
        Save a result to the cache.
        Skips REFUSED, low-confidence, and short answers.
        """
        try:
            # ─────────────────────────────────────────────────────
            # SAFETY CHECK: Never cache bad results
            # ─────────────────────────────────────────────────────
            decision = getattr(result, "decision", None)
            confidence = getattr(result, "confidence", 0.0) or 0.0
            answer = getattr(result, "answer", "") or ""

            if decision == "REFUSED":
                print(f"[CacheManager] Skipping cache: REFUSED decision")
                return False

            if confidence < MIN_CONFIDENCE_TO_CACHE:
                print(f"[CacheManager] Skipping cache: confidence too low ({confidence:.2f})")
                return False

            if len(answer) < MIN_ANSWER_LENGTH_TO_CACHE:
                print(f"[CacheManager] Skipping cache: answer too short ({len(answer)} chars)")
                return False

            # ─────────────────────────────────────────────────────
            # Save to cache
            # ─────────────────────────────────────────────────────
            key = generate_cache_key(question, language, country)
            normalized = normalize_question(question)

            sources_json = json.dumps(
                [s.dict() if hasattr(s, "dict") else str(s) for s in getattr(result, "sources", [])],
                default=str,
            )
            claims_json = json.dumps(
                [c.dict() if hasattr(c, "dict") else str(c) for c in getattr(result, "claims", [])],
                default=str,
            )
            verification_json = json.dumps(
                result.verification.dict() if hasattr(result.verification, "dict") else {},
                default=str,
            )

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO response_cache
                (cache_key, question, normalized_question, language, country,
                 answer, sources_json, claims_json, verification_json,
                 confidence, decision, created_at, last_used_at, hit_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE(
                    (SELECT hit_count FROM response_cache WHERE cache_key = ?), 0
                ))
            """, (
                key, question, normalized, language, country,
                answer,
                sources_json, claims_json, verification_json,
                confidence,
                decision or "PASS",
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                key,
            ))
            conn.commit()
            conn.close()

            print(f"[CacheManager] ✅ Cached: {question[:60]}...")
            self._enforce_size_limit()
            return True
        except Exception as e:
            print(f"[CacheManager] set error: {e}")
            return False

    def _enforce_size_limit(self):
        """If cache exceeds max entries, delete least-recently-used."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM response_cache")
        count = cursor.fetchone()[0]

        if count > MAX_CACHE_ENTRIES:
            to_delete = count - MAX_CACHE_ENTRIES
            cursor.execute("""
                DELETE FROM response_cache WHERE id IN (
                    SELECT id FROM response_cache
                    ORDER BY last_used_at ASC
                    LIMIT ?
                )
            """, (to_delete,))
            conn.commit()

        conn.close()

    def stats(self) -> Dict[str, Any]:
        """Return cache statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*), SUM(hit_count) FROM response_cache")
        row = cursor.fetchone()
        conn.close()
        return {
            "total_entries": row[0] or 0,
            "total_hits": row[1] or 0,
        }

    def clear(self) -> int:
        """Delete all cache entries. Returns count deleted."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM response_cache")
        count = cursor.fetchone()[0]
        cursor.execute("DELETE FROM response_cache")
        conn.commit()
        conn.close()
        return count

    def clear_expired(self) -> int:
        """Delete expired entries. Returns count deleted."""
        cutoff = (datetime.now() - timedelta(days=DEFAULT_TTL_DAYS)).isoformat()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM response_cache WHERE created_at < ?", (cutoff,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted

    def clear_refused(self) -> int:
        """Delete all REFUSED entries from cache. Returns count deleted."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM response_cache WHERE decision = 'REFUSED'")
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted

    def top_questions(self, limit: int = 10) -> list:
        """Return top asked questions."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT question, hit_count, confidence, decision, created_at
            FROM response_cache
            ORDER BY hit_count DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [
            {"question": r[0], "hits": r[1], "confidence": r[2], "decision": r[3], "created_at": r[4]}
            for r in rows
        ]