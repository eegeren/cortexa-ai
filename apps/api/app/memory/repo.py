from __future__ import annotations
from typing import List, Tuple, Dict, Any
from sqlalchemy import text
from app.db.base import SessionLocal, engine

# ilk boot’ta tablo/vectors uzantısı
def ensure_schema():
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL DEFAULT ''
        )
        """))
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS memories (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            user_id UUID NOT NULL,
            kind TEXT NOT NULL,
            content TEXT NOT NULL,
            embedding vector(1536) NOT NULL,
            meta JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_mem_user ON memories(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_mem_embed ON memories USING ivfflat (embedding vector_l2_ops)"))
ensure_schema()

def upsert_memory(user_id: str, kind: str, content: str, emb: list[float], meta: Dict[str, Any]):
    vec = "[" + ",".join(f"{x:.8f}" for x in emb) + "]"
    with SessionLocal() as db:
        db.execute(text("""
            INSERT INTO memories (user_id, kind, content, embedding, meta)
            VALUES (:uid, :k, :c, CAST(:e AS vector), CAST(:m AS jsonb))
        """), {"uid": user_id, "k": kind, "c": content, "e": vec, "m": meta})
        db.commit()

def search_memories(user_id: str, query_emb: list[float], k: int = 5, max_dist: float = 0.4) -> List[Tuple[str, Dict[str, Any]]]:
    vec = "[" + ",".join(f"{x:.8f}" for x in query_emb) + "]"
    with SessionLocal() as db:
        rows = db.execute(text("""
            SELECT content, meta, (embedding <-> CAST(:q AS vector)) AS dist
            FROM memories
            WHERE user_id = :uid
            ORDER BY dist ASC
            LIMIT :k
        """), {"uid": user_id, "q": vec, "k": k}).all()
        return [(r.content, r.meta) for r in rows if r.dist is None or r.dist <= max_dist]