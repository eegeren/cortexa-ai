from typing import List
import httpx
from app.config import settings

MODEL = "text-embedding-3-small"

async def embed_texts(texts: List[str]) -> List[List[float]]:
    headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
    payload = {"model": MODEL, "input": texts}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post("https://api.openai.com/v1/embeddings", headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        return [item["embedding"] for item in data["data"]]