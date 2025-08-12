# app/memory/auto.py
from __future__ import annotations
import os, hashlib, asyncio
from typing import List, Dict
import httpx
from app.memory.repo import insert_memory

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
EXTRACT_MODEL = os.getenv("OPENAI_EXTRACT_MODEL", "gpt-4o-mini")

# Basit bir normalizasyon: boşluk kırp, küçük harf vs.
def _normalize(v: str) -> str:
    return " ".join(v.strip().split())

def _content_hash(user_id: str, kind: str, content: str) -> str:
    h = hashlib.sha256()
    h.update((user_id + "|" + kind + "|" + _normalize(content)).encode("utf-8"))
    return h.hexdigest()

async def _extract_candidates(message: str) -> List[Dict]:
    """
    Modelden sade bir JSON listesi istiyoruz. Örnek:
    [
      {"kind":"profile","content":"Kullanıcının adı Yusuf","meta":{"source":"chat","confidence":0.86}},
      {"kind":"preference","content":"iOS geliştiricisi","meta":{"confidence":0.8}}
    ]
    """
    if not OPENAI_API_KEY:
        return []

    sys = (
        "You extract long-lived user facts for a memory store.\n"
        "Return ONLY a valid JSON array. Items keep it short and factual.\n"
        "Allowed kinds: profile, preference, fact, task, company, contact.\n"
        "Ignore ephemeral or speculative info."
    )
    prompt = [
        {"role":"system","content": sys},
        {"role":"user","content": f"Message:\n{message}\n\nExtract memory items as JSON array."}
    ]

    async with httpx.AsyncClient(timeout=40) as client:
        r = await client.post(
            f"{OPENAI_API_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={"model": EXTRACT_MODEL, "messages": prompt, "temperature": 0.0},
        )
        r.raise_for_status()
        txt = r.json()["choices"][0]["message"]["content"]

    # Minimum dayanıklı JSON parse
    import json
    try:
        data = json.loads(txt)
        if isinstance(data, list):
            # normalize & alanları garanti altına al
            out = []
            for it in data:
                kind = (it.get("kind") or "fact").strip().lower()
                content = _normalize(it.get("content") or "")
                if not content:
                    continue
                meta = it.get("meta") or {}
                # Güven eşiği yoksa 0.5 ver
                conf = float(meta.get("confidence", 0.5))
                out.append({"kind": kind, "content": content, "meta": {"confidence": conf}})
            return out[:8]  # Güvenli limit
    except Exception:
        return []
    return []

async def auto_remember(user_id: str, raw_user_message: str):
    """
    Arkada çalışır. Çıkar, filtrele, dedupe et ve DB'ye ekle.
    """
    candidates = await _extract_candidates(raw_user_message)
    if not candidates:
        return

    # Basit filtre: confidence < 0.55 at
    kept = [c for c in candidates if c["meta"].get("confidence", 0.5) >= 0.55]
    if not kept:
        return

    # Dedupe: aynı mesaj içinde tekrarları tutma
    seen = set()
    final = []
    for c in kept:
        key = (c["kind"], c["content"].lower())
        if key in seen:
            continue
        seen.add(key)
        final.append(c)

    # Yaz
    for c in final:
        # İçerik hash'i üzerinden “yumuşak” dedupe (aynı kayıt varsa es geç)
        h = _content_hash(user_id, c["kind"], c["content"])
        meta = dict(c.get("meta", {}))
        meta["hash"] = h
        try:
            await asyncio.to_thread(
                insert_memory, user_id, c["kind"], c["content"], [], meta  # emb [] versek de repo embedliyor olabilir; yoksa orayı çağırma
            )
        except Exception:
            # Hata olursa sessiz geç
            continue