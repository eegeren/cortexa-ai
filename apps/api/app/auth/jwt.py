import os, time, jwt
JWT_SECRET = os.getenv("JWT_SECRET", "devsecret")

def create_token(user_id: str, ttl_sec: int = 60*60*24*30):
    now = int(time.time())
    payload = {"sub": user_id, "iat": now, "exp": now + ttl_sec}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")