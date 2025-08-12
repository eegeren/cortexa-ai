from __future__ import annotations

import os, jwt, httpx, asyncio, logging, json
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from app.memory.repo import search_memories, upsert_memory
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])

def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid token")
    uid = payload.get("sub")
    if not uid:
        raise HTTPException(401, "Invalid token payload")
    return type("User", (), {"id": uid})

async def embed_text(text_in: str) -> list[float]:
    if not settings.OPENAI_API_KEY:
        raise HTTPException(500, "OPENAI_API_KEY missing")
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            f"{settings.OPENAI_API_BASE}/embeddings",
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
            json={"model": settings.OPENAI_EMBED_MODEL, "input": text_in},
        )
        r.raise_for_status()
        return r.json()["data"][0]["embedding"]

async def chat_completion(messages: list[dict], temperature: float = 0.3) -> str:
    if not settings.OPENAI_API_KEY:
        raise HTTPException(500, "OPENAI_API_KEY missing")
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(
            f"{settings.OPENAI_API_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
            json={"model": settings.OPENAI_MODEL, "messages": messages, "temperature": temperature},
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

async def extract_facts(text_in: str) -> list[dict]:
    prompt = (
        "Metinden kullanici hakkinda KISA ve kalici olabilecek gercekler cikar.\n"
        "JSON liste don: [{'kind':'profile|preference|note','content':'...','score':0..1}, ...]\n"
        f"Metin: {text_in}"
    )
    msg = [{"role": "system", "content": "You extract short user facts."},
           {"role": "user", "content": prompt}]
    try:
        out = await chat_completion(msg, temperature=0.1)
        facts = json.loads(out)
        return facts if isinstance(facts, list) else []
    except Exception as e:
        logger.warning(f"[extract_facts] fallback: {e}")
        return []

class ChatIn(BaseModel):
    message: str

@router.post("/complete")
async def complete(payload: ChatIn, user=Depends(get_current_user)):
    # recall
    qemb = await embed_text(payload.message)
    mems = [c for c, _ in search_memories(user.id, qemb, k=8, max_dist=settings.RECALL_MAX_DIST)]
    logger.info(f"[chat] uid={user.id} recall={len(mems)} preview={mems[:2]}")

    memory_block = "\n".join(f"- {m}" for m in mems) if mems else "- (no memory)"
    system = (
        "You are Cortexa. If relevant, use the user's stored context.\n"
        "User context:\n" + memory_block
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": payload.message},
    ]

    reply = await chat_completion(messages, temperature=0.3)

    # auto memory (fire-and-forget)
    async def _auto_store():
        try:
            facts = await extract_facts(payload.message)
            filtered = []
            for f in facts:
                content = (f or {}).get("content", "").strip()
                if len(content) < 10:
                    continue
                score = float((f or {}).get("score", 0))
                if score < settings.AUTO_MEMORY_MIN_SCORE:
                    continue
                kind = (f or {}).get("kind") or "note"
                filtered.append({"kind": kind, "content": content, "score": score})
            if not filtered:
                return
            embs = await asyncio.gather(*[embed_text(it["content"]) for it in filtered])
            for it, emb in zip(filtered, embs):
                upsert_memory(
                    user.id, it["kind"], it["content"], emb,
                    {"source": "auto", "score": it["score"]}
                )
            logger.info(f"[auto-mem] uid={user.id} stored={len(filtered)}")
        except Exception as e:
            logger.warning(f"[auto-mem] skip: {e}")

    asyncio.create_task(_auto_store())
    return {"reply": reply, "memories_used": mems}