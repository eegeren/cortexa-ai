# app/memory/extract.py
from __future__ import annotations
import os
import httpx
import json
import re
from typing import List, Dict

# --- OpenAI ayarları (seninkiyle aynı) ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_EXTRACT_MODEL = os.getenv("OPENAI_EXTRACT_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = (
    "You extract long-lived user facts for a personal memory store.\n"
    "Rules:\n"
    "- Return ONLY a valid JSON array (no prose).\n"
    '- Each item: {"kind": "profile|preference|fact|task|company|contact|note", '
    '"content": string, "score": number in [0,1]}.\n'
    '- Keep content short, factual, first-person normalized if needed (e.g., "Adim Yusuf.").\n'
    "- Ignore ephemeral info (greetings, small talk) and speculation.\n"
    "- Prefer Turkish output for content if the user wrote Turkish.\n"
)

# --- Basit yerel çıkarım (fallback) ---
_NAME_RE = re.compile(r"\b(?:benim\s+ad[ıi]m|ad[ıi]m)\s+(?P<name>[A-Za-zçğıöşüÇĞİÖŞÜ]+)\b", re.IGNORECASE)
_AGE_RE  = re.compile(r"\b(?P<age>\d{1,2})\s*yaş(?:ındayım|ınday[ıi]m|ında|ım|im)?\b", re.IGNORECASE)
_JOB_RE  = re.compile(
    r"\b(iOS|Android|frontend|back[- ]?end|full[- ]?stack|veri bilimi|data science|ml|ai|"
    r"yapay zeka|yaz[ıi]l[ıi]m gel[ıi]şt[ıi]r[ıi]c[ıi]s[ıi]y[ıi]m|mobil gel[ıi]ştiriciyim)\b",
    re.IGNORECASE,
)

def _norm(t: str) -> str:
    return " ".join((t or "").strip().split())

def _regex_fallback(message: str) -> List[Dict]:
    """Model çökünce en azından çekirdek kişisel bilgiler dönelim."""
    t = message or ""
    out: List[Dict] = []

    m = _NAME_RE.search(t)
    if m:
        name = _norm(m.group("name"))
        if name:
            out.append({"kind": "profile", "content": f"Kullanıcının adı {name}.", "score": 0.9})

    m = _AGE_RE.search(t)
    if m:
        age = m.group("age")
        out.append({"kind": "profile", "content": f"Kullanıcı {age} yaşında.", "score": 0.85})

    m = _JOB_RE.search(t)
    if m:
        job = _norm(m.group(0))
        out.append({"kind": "profile", "content": f"Kullanıcının alanı/işi: {job}.", "score": 0.75})

    # ipucu varsa ve hiçbir şey yakalayamadıysak ham notu düşük skorla kaydet
    if not out and any(k in t.lower() for k in ["adım", "yaş", "meslek", "öğrenci", "geliştirici"]):
        out.append({"kind": "note", "content": _norm(t), "score": 0.6})

    return out[:8]


async def extract_facts(message: str) -> List[Dict]:
    """
    Kullanıcı mesajından kalıcı olabilecek bilgiler çıkarır.
    1) OpenAI'den yapılandırılmış JSON dene
    2) Boş/başarısız ise regex fallback kullan
    DÖNÜŞ: [{kind, content, score}, ...]
    """
    # --- A) OpenAI yolu ---
    if OPENAI_API_KEY:
        payload = {
            "model": OPENAI_EXTRACT_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Message:\n{message}\n\nJSON array only."}
            ],
            "temperature": 0.0,
        }

        try:
            async with httpx.AsyncClient(timeout=45) as client:
                r = await client.post(
                    f"{OPENAI_API_BASE}/chat/completions",
                    headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                    json=payload,
                )
                r.raise_for_status()
                content = r.json()["choices"][0]["message"]["content"]
            try:
                data = json.loads(content)
                if isinstance(data, list) and data:
                    out: List[Dict] = []
                    for it in data:
                        kind = (it.get("kind") or "note").strip().lower()
                        text = (it.get("content") or "").strip()
                        score = float(it.get("score", 0.6))
                        if not text:
                            continue
                        if kind not in {"profile", "preference", "fact", "task", "company", "contact", "note"}:
                            kind = "note"
                        score = max(0.0, min(1.0, score))
                        out.append({"kind": kind, "content": text, "score": score})
                    # OpenAI’den bir şey çıktıysa direkt dön
                    if out:
                        return out[:8]
            except Exception:
                pass  # JSON bozuksa fallback'e düşeceğiz

        except httpx.HTTPError:
            # network/rate limit vs. => fallback'e düş
            pass

    # --- B) Regex fallback ---
    return _regex_fallback(message)