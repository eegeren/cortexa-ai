from fastapi import Header, HTTPException
from app.auth.jwt import verify_token

async def current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing token")
    uid = verify_token(authorization.replace("Bearer ", "").strip())
    if not uid:
        raise HTTPException(401, "Invalid token")
    return uid