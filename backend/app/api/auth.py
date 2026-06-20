from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User

from jose import jwt
from datetime import datetime, timedelta

from pydantic import BaseModel, EmailStr
import bcrypt

import requests

router = APIRouter()

from app.config import SECRET_KEY

def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False

# =========================
# Request Schemas
# =========================

class GoogleAuthRequest(BaseModel):
    access_token: str


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# =========================
# JWT Helper
# =========================

def create_token(user_id: int, email: str, name: str) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "name": name,
        "exp": datetime.utcnow() + timedelta(days=7)
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


# =========================
# Register
# =========================

@router.post("/register")
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    existing_user = (
        db.query(User)
        .filter(User.email == request.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    user = User(
        name=request.name,
        email=request.email,
        hashed_password=hash_password(
            request.password
        )
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_token(
        user.id,
        user.email,
        user.name
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name
        }
    }


# =========================
# Login
# =========================

@router.post("/login")
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(User.email == request.email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Prevent password login for Google accounts
    if user.hashed_password == "GOOGLE_USER":
        raise HTTPException(
            status_code=400,
            detail="Please sign in with Google"
        )

    if not verify_password(
        request.password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    token = create_token(
        user.id,
        user.email,
        user.name
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name
        }
    }


# =========================
# Google Login
# =========================

@router.post("/google")
def google_auth(
    request: GoogleAuthRequest,
    db: Session = Depends(get_db)
):
    response = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={
            "Authorization": f"Bearer {request.access_token}"
        }
    )

    if response.status_code != 200:
        raise HTTPException(
            status_code=401,
            detail="Invalid Google token"
        )

    google_user = response.json()

    email = google_user.get("email")
    name = google_user.get("name")

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Could not get email from Google"
        )

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if not user:
        user = User(
            email=email,
            name=name or email.split("@")[0],
            hashed_password="GOOGLE_USER"
        )

        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_token(
        user.id,
        user.email,
        user.name
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name
        }
    }