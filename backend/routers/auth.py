from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
import uuid
import os

from database import get_db
from auth import hash_password, verify_password, create_access_token, get_current_user
import models

from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request

limiter = Limiter(key_func=get_remote_address)

def get_limit():
    if os.getenv("TESTING") == "true":
        return "1000/minute"
    return "10/minute"

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: models.UserRole


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    full_name: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str

    model_config = {"from_attributes": True}


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(get_limit())
async def register(request: Request, body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).where(models.User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = models.User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        role=body.role,
    )
    db.add(user)
    await db.flush()

    if body.role == models.UserRole.candidate:
        profile = models.CandidateProfile(user_id=user.id)
        db.add(profile)

    await db.commit()

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        role=user.role.value,
        full_name=user.full_name,
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit(get_limit())
async def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).where(models.User.email == form.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        role=user.role.value,
        full_name=user.full_name,
    )


@router.get("/me", response_model=UserResponse)
async def me(current_user: models.User = Depends(get_current_user)):
    return current_user