from __future__ import annotations
import os, jwt, uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from passlib.hash import bcrypt
from sqlalchemy import text
from app.db.base import SessionLocal
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

def create_token(sub: str) -> str:
    return jwt.encode({"sub": sub}, settings.JWT_SECRET, algorithm="HS256")

class RegisterIn(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    token: str

@router.post("/register", response_model=TokenOut)
def register(data: RegisterIn):
    with SessionLocal() as db:
        phash = bcrypt.hash(data.password)
        try:
            uid = db.execute(text("""
                INSERT INTO users (email, password_hash)
                VALUES (:email, :phash) RETURNING id
            """), {"email": data.email, "phash": phash}).scalar_one()
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(400, "Email already exists")
    return {"token": create_token(str(uid))}

class LoginIn(BaseModel):
    email: EmailStr
    password: str

@router.post("/login", response_model=TokenOut)
def login(data: LoginIn):
    with SessionLocal() as db:
        row = db.execute(text(
            "SELECT id, password_hash FROM users WHERE email=:e"
        ), {"e": data.email}).first()
        if not row or not bcrypt.verify(data.password, row.password_hash):
            raise HTTPException(401, "Invalid credentials")
        return {"token": create_token(str(row.id))}

@router.post("/guest", response_model=TokenOut)
def guest():
    # anonim kullanıcıyı (varsa) tablodan bul, yoksa oluştur
    with SessionLocal() as db:
        uid = db.execute(text("""
            INSERT INTO users (email, password_hash)
            VALUES (:email, '')
            ON CONFLICT (email) DO UPDATE SET email = EXCLUDED.email
            RETURNING id
        """), {"email": "guest@cortexa.local"}).scalar_one()
        db.commit()
    return {"token": create_token(str(uid))}