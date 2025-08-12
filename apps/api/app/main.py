from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.utils.logging import RequestIDMiddleware
from app.auth.routes import router as auth_router
from app.memory.routes import router as memory_router
from app.chat.routes import router as chat_router
import os

app = FastAPI(title="Cortexa API")

# --- CORS ---
ENV = os.getenv("ENV", "production")

ALLOWED_ORIGINS = [
    "https://chat.coinspacetech.net",
    "https://coinspacetech.net",
    "https://www.coinspacetech.net",
]

# Geliştirme ortamı (opsiyonel)
if ENV != "production":
    ALLOWED_ORIGINS += [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

app.add_middleware(RequestIDMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app$",  # Vercel preview domainleri
    allow_credentials=True,  # cookie/token cross-site için gerekli
    allow_methods=["*"],
    allow_headers=["*"],
    # expose_headers=["X-Request-ID"],  # İstersen istemci görsün
)

@app.get("/health")
def health():
    return {"ok": True}

app.include_router(auth_router)
app.include_router(memory_router)
app.include_router(chat_router)