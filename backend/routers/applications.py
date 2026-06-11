from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import uuid
from uuid import UUID
from datetime import datetime

from database import get_db
from auth import get_current_user, require_role
import models

router = APIRouter()

from services.cover_letter import generate_cover_letter

class ApplicationCreate(BaseModel):
    job_id: UUID
    cover_note: str = ""


class ApplicationResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    candidate_id: uuid.UUID
    status: str
    cover_note: str
    applied_at: datetime
    job_title: str = ""
    job_company: str = ""
    job_is_active: bool = True
    candidate_name: str = ""
    candidate_email: str = ""
    candidate_resume_url: str = ""
    match_score: float = 0.0

    model_config = {"from_attributes": True}


class StatusUpdate(BaseModel):
    status: models.ApplicationStatus

class CoverLetterRequest(BaseModel):
    job_id: UUID


class CoverLetterResponse(BaseModel):
    cover_letter: str


@router.post("/generate-cover-letter", response_model=CoverLetterResponse)
async def generate_cover_letter_endpoint(
    body: CoverLetterRequest,
    current_user: models.User = Depends(require_role(models.UserRole.candidate)),
    db: AsyncSession = Depends(get_db),
):
    # Get job details
    result = await db.execute(select(models.Job).where(models.Job.id == body.job_id))
    job = result.scalar_one_or_none()
    if not job or not job.is_active:
        raise HTTPException(status_code=404, detail="Job not found")

    # Get candidate resume text
    result = await db.execute(
        select(models.CandidateProfile).where(
            models.CandidateProfile.user_id == current_user.id
        )
    )
    profile = result.scalar_one_or_none()
    if not profile or not profile.resume_text:
        raise HTTPException(
            status_code=400,
            detail="Upload your resume first to generate a cover letter"
        )

    cover_letter = await generate_cover_letter(
        resume_text=profile.resume_text,
        job_title=job.title,
        company=job.company,
        job_description=job.description,
        job_requirements=job.requirements,
    )

    return CoverLetterResponse(cover_letter=cover_letter)

@router.post("/", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def apply(
    body: ApplicationCreate,
    current_user: models.User = Depends(require_role(models.UserRole.candidate)),
    db: AsyncSession = Depends(get_db),
):
    # Check job exists and is active
    result = await db.execute(select(models.Job).where(models.Job.id == body.job_id))
    job = result.scalar_one_or_none()
    if not job or not job.is_active:
        raise HTTPException(status_code=404, detail="Job not found or inactive")

    # Check not already applied
    result = await db.execute(
        select(models.Application).where(
            models.Application.candidate_id == current_user.id,
            models.Application.job_id == body.job_id,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already applied to this job")

    application = models.Application(
        candidate_id=current_user.id,
        job_id=body.job_id,
        cover_note=body.cover_note,
    )
    db.add(application)
    await db.commit()
    await db.refresh(application)
    return application


@router.get("/my-applications", response_model=list[ApplicationResponse])
async def my_applications(
    current_user: models.User = Depends(require_role(models.UserRole.candidate)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(models.Application, models.Job)
        .join(models.Job, models.Application.job_id == models.Job.id)
        .where(models.Application.candidate_id == current_user.id)
        .order_by(models.Application.applied_at.desc())
    )
    rows = result.all()
    applications = []
    for app, job in rows:
        applications.append(ApplicationResponse(
            id=app.id,
            job_id=app.job_id,
            candidate_id=app.candidate_id,
            status=app.status,
            cover_note=app.cover_note,
            applied_at=app.applied_at,
            job_title=job.title,
            job_company=job.company,
            job_is_active=job.is_active,
        ))
    return applications


@router.get("/job/{job_id}", response_model=list[ApplicationResponse])
async def applications_for_job(
    job_id: UUID,
    current_user: models.User = Depends(require_role(models.UserRole.recruiter)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(models.Job).where(models.Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job or job.recruiter_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await db.execute(
        select(models.Application, models.User, models.CandidateProfile)
        .join(models.User, models.Application.candidate_id == models.User.id)
        .join(models.CandidateProfile, models.CandidateProfile.user_id == models.User.id)
        .where(models.Application.job_id == job_id)
        .order_by(models.Application.applied_at.desc())
    )
    rows = result.all()

    applications = []
    for app, user, profile in rows:
        # Compute cosine similarity between job and candidate embeddings
        match_score = 0.0
        if job.embedding is not None and profile.embedding is not None:
            import numpy as np
            job_vec = np.array(job.embedding)
            cand_vec = np.array(profile.embedding)
            match_score = float(np.dot(job_vec, cand_vec) / (np.linalg.norm(job_vec) * np.linalg.norm(cand_vec)))

        applications.append(ApplicationResponse(
            id=app.id,
            job_id=app.job_id,
            candidate_id=app.candidate_id,
            status=app.status,
            cover_note=app.cover_note,
            applied_at=app.applied_at,
            candidate_name=user.full_name,
            candidate_email=user.email,
            candidate_resume_url=profile.resume_url or "",
            match_score=round(match_score, 4),
        ))

    # Sort by match score descending
    applications.sort(key=lambda x: x.match_score, reverse=True)
    return applications


@router.patch("/{application_id}/status", response_model=ApplicationResponse)
async def update_status(
    application_id: UUID,
    body: StatusUpdate,
    current_user: models.User = Depends(require_role(models.UserRole.recruiter)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(models.Application).where(models.Application.id == application_id)
    )
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Verify recruiter owns the job
    result = await db.execute(
        select(models.Job).where(models.Job.id == application.job_id)
    )
    job = result.scalar_one_or_none()
    if job.recruiter_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    application.status = body.status
    await db.commit()
    await db.refresh(application)
    return application