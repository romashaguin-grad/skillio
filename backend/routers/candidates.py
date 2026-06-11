from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
import uuid
import json

from database import get_db
from auth import get_current_user, require_role
from services.resume_parser import parse_resume
from services.embedding import generate_embedding
from services.storage import upload_file
import models

from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request

limiter = Limiter(key_func=get_remote_address)

router = APIRouter()


class ProfileResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    bio: str
    skills: list[str]
    experience: str
    education: str
    resume_url: str

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    bio: Optional[str] = None
    skills: Optional[list[str]] = None
    experience: Optional[str] = None
    education: Optional[str] = None


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    current_user: models.User = Depends(require_role(models.UserRole.candidate)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(models.CandidateProfile).where(
            models.CandidateProfile.user_id == current_user.id
        )
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.patch("/profile", response_model=ProfileResponse)
async def update_profile(
    body: ProfileUpdate,
    current_user: models.User = Depends(require_role(models.UserRole.candidate)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(models.CandidateProfile).where(
            models.CandidateProfile.user_id == current_user.id
        )
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    update_data = body.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    # Regenerate embedding from updated profile text
    profile_text = f"{profile.bio} {' '.join(profile.skills or [])} {profile.experience} {profile.education}"
    profile.embedding = await generate_embedding(profile_text)

    await db.commit()
    await db.refresh(profile)
    return profile


@router.post("/profile/resume", response_model=ProfileResponse)
@limiter.limit("5/minute")
async def upload_resume(request: Request,
    file: UploadFile = File(...),
    current_user: models.User = Depends(require_role(models.UserRole.candidate)),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF resumes are accepted")

    contents = await file.read()

    # Upload to storage and get URL
    resume_url = await upload_file(contents, file.filename, current_user.id)

    # Parse resume with pdfplumber + Gemini
    parsed = await parse_resume(contents)

    result = await db.execute(
        select(models.CandidateProfile).where(
            models.CandidateProfile.user_id == current_user.id
        )
    )
    profile = result.scalar_one_or_none()

    # Auto-populate profile from parsed resume
    profile.resume_url = resume_url
    profile.resume_text = parsed.get("raw_text", "")
    profile.bio = parsed.get("summary", profile.bio)
    profile.skills = parsed.get("skills", profile.skills)
    profile.experience = json.dumps(parsed.get("experience", []))
    profile.education = json.dumps(parsed.get("education", []))

    # Generate embedding from resume text
    profile_text = f"{profile.bio} {' '.join(profile.skills or [])} {profile.resume_text}"
    profile.embedding = await generate_embedding(profile_text)

    await db.commit()
    await db.refresh(profile)
    return profile