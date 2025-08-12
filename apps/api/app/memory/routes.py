from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from app.memory.repo import upsert_memory, search_memories
from app.config import settings
import jwt

router = APIRouter(prefix="/memory", tags=["memory"])

def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid token")
    return type("User", (), {"id": payload.get("sub")})

class UpsertIn(BaseModel):
    kind: str
    content: str
    meta: dict = {}

@router.post("/upsert")
def upsert(payload: UpsertIn, user=Depends(get_current_user)):
    # burada embed’i FE veriyorsa kabul edebilirdik; şimdilik sadece text alıyoruz
    raise HTTPException(501, "Use /chat/complete for automatic memory")