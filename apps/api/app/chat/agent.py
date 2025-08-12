import httpx
from app.config import settings

SYSTEM_PROMPT = """You are Cortexa, a helpful personal AI.
Use relevant long-term memories if provided. Be concise and actionable."""

async def complete_with_memories(user_msg: str, memories: list[str]) -> str:
    mem_text = "\n".join(memories[:5]) if memories else "No memory."
    messages = [
        {"role":"system","content": SYSTEM_PROMPT},
        {"role":"system","content": f"Relevant memories:\n{mem_text}"},
        {"role":"user","content": user_msg},
    ]
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
            json={"model":"gpt-4.1-mini","messages":messages,"temperature":0.3})
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"].strip()