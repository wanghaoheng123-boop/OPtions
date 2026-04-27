import json
import sqlite3
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "vector_rag" / "embeddings.db"


class SQLiteFTSStore:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS rag_chunks USING fts5(
                  doc_id,
                  chunk_id,
                  domain,
                  source_path,
                  chunk_text,
                  metadata_json,
                  tokenize='unicode61'
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS rag_chunk_meta (
                  chunk_id TEXT PRIMARY KEY,
                  doc_id TEXT NOT NULL,
                  source_path TEXT NOT NULL,
                  domain TEXT NOT NULL,
                  metadata_json TEXT NOT NULL,
                  created_at_utc TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def clear_doc(self, doc_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM rag_chunks WHERE doc_id = ?", (doc_id,))
            conn.execute("DELETE FROM rag_chunk_meta WHERE doc_id = ?", (doc_id,))
            conn.commit()

    def insert_chunk(
        self,
        doc_id: str,
        chunk_id: str,
        domain: str,
        source_path: str,
        chunk_text: str,
        metadata: dict,
        created_at_utc: str,
    ) -> None:
        metadata_json = json.dumps(metadata, sort_keys=True)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO rag_chunks (doc_id, chunk_id, domain, source_path, chunk_text, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (doc_id, chunk_id, domain, source_path, chunk_text, metadata_json),
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO rag_chunk_meta (
                  chunk_id, doc_id, source_path, domain, metadata_json, created_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (chunk_id, doc_id, source_path, domain, metadata_json, created_at_utc),
            )
            conn.commit()

    def similarity_search(self, query: str, top_k: int = 5) -> Iterable[sqlite3.Row]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                  doc_id,
                  chunk_id,
                  domain,
                  source_path,
                  snippet(rag_chunks, 4, '[', ']', '...', 16) AS snippet,
                  bm25(rag_chunks) AS score
                FROM rag_chunks
                WHERE rag_chunks MATCH ?
                ORDER BY score
                LIMIT ?
                """,
                (query, top_k),
            ).fetchall()
        return rows

    def count_chunks(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM rag_chunks").fetchone()
        return int(row["c"])
