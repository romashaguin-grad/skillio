from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
import uuid
from datetime import datetime

from database import get_db
from auth import get_current_user, require_role
from services.embedding import generate_embedding
import models

router = APIRouter()


class JobCreate(BaseModel):
    title: str
    company: str
    location: str = "Remote"
    description: str
    requirements: str = ""
    salary_range: str = ""
    job_type: str = "Full-time"


class JobResponse(BaseModel):
    id: uuid.UUID
    title: str
    company: str
    location: str
    description: str
    requirements: str
    salary_range: str
    job_type: str
    is_active: bool
    created_at: datetime
    recruiter_id: uuid.UUID

    model_config = {"from_attributes": True}


@router.get("/", response_model=list[JobResponse])
async def list_jobs(
    skip: int = 0,
    limit: int = 20,
    search: str = "",
    location: str = "",
    job_type: str = "",
    db: AsyncSession = Depends(get_db),
):
    query = select(models.Job).where(models.Job.is_active == True)

    if search:
        query = query.where(
            models.Job.title.ilike(f"%{search}%") |
            models.Job.description.ilike(f"%{search}%") |
            models.Job.requirements.ilike(f"%{search}%")
        )
    if location:
        query = query.where(models.Job.location.ilike(f"%{location}%"))
    if job_type:
        query = query.where(models.Job.job_type == job_type)

    query = query.order_by(models.Job.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Job).where(models.Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    body: JobCreate,
    current_user: models.User = Depends(require_role(models.UserRole.recruiter)),
    db: AsyncSession = Depends(get_db),
):
    # Generate embedding from title + description + requirements
    text = f"{body.title} {body.description} {body.requirements}"
    embedding = await generate_embedding(text)

    job = models.Job(
        recruiter_id=current_user.id,
        embedding=embedding,
        **body.model_dump(),
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


@router.patch("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: UUID,
    body: JobCreate,
    current_user: models.User = Depends(require_role(models.UserRole.recruiter)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(models.Job).where(models.Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.recruiter_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your job posting")

    for field, value in body.model_dump().items():
        setattr(job, field, value)

    text = f"{body.title} {body.description} {body.requirements}"
    job.embedding = await generate_embedding(text)

    await db.commit()
    await db.refresh(job)
    return job


@router.patch("/{job_id}/toggle", response_model=JobResponse)
async def toggle_job(
    job_id: UUID,
    current_user: models.User = Depends(require_role(models.UserRole.recruiter)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(models.Job).where(models.Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.recruiter_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your job posting")
    job.is_active = not job.is_active
    await db.commit()
    await db.refresh(job)
    return job


@router.get("/recruiter/my-jobs", response_model=list[JobResponse])
async def my_jobs(
    current_user: models.User = Depends(require_role(models.UserRole.recruiter)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(models.Job)
        .where(models.Job.recruiter_id == current_user.id)
        .order_by(models.Job.created_at.desc())
    )
    return result.scalars().all()