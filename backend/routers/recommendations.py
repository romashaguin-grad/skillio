from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from pydantic import BaseModel
import uuid
from datetime import datetime

from database import get_db
from auth import require_role
import models

from uuid import UUID

router = APIRouter()


class RecommendedJob(BaseModel):
    id: uuid.UUID
    title: str
    company: str
    location: str
    description: str
    requirements: str
    salary_range: str
    job_type: str
    created_at: datetime
    similarity_score: float


@router.get("/", response_model=list[RecommendedJob])
async def get_recommendations(
    limit: int = 10,
    current_user: models.User = Depends(require_role(models.UserRole.candidate)),
    db: AsyncSession = Depends(get_db),
):
    # Get candidate profile with embedding
    result = await db.execute(
        select(models.CandidateProfile).where(
            models.CandidateProfile.user_id == current_user.id
        )
    )
    profile = result.scalar_one_or_none()

    if not profile or profile.embedding is None:
        raise HTTPException(
            status_code=400,
            detail="Upload your resume first to get recommendations",
        )

    # pgvector cosine similarity search
    query = text("""
        SELECT
            id,
            title,
            company,
            location,
            description,
            requirements,
            salary_range,
            job_type,
            created_at,
            1 - (embedding <=> CAST(:candidate_embedding AS vector)) AS similarity_score
        FROM jobs
        WHERE is_active = true
          AND embedding IS NOT NULL
        ORDER BY embedding <=> CAST(:candidate_embedding AS vector)
        LIMIT :limit
    """)

    embedding_str = "[" + ",".join(str(x) for x in profile.embedding) + "]"
    rows = await db.execute(query, {"candidate_embedding": embedding_str, "limit": limit})
    results = rows.mappings().all()

    return [RecommendedJob(
        id=row["id"],
        title=row["title"],
        company=row["company"],
        location=row["location"],
        description=row["description"],
        requirements=row["requirements"],
        salary_range=row["salary_range"],
        job_type=row["job_type"],
        created_at=row["created_at"],
        similarity_score=float(row["similarity_score"]),
    ) for row in results]

class SkillGapResponse(BaseModel):
    missing_skills: list[str]
    matching_skills: list[str]
    match_score: float


@router.get("/skill-gap/{job_id}", response_model=SkillGapResponse)
async def skill_gap(
    job_id: UUID,
    current_user: models.User = Depends(require_role(models.UserRole.candidate)),
    db: AsyncSession = Depends(get_db),
):
    # Get job
    result = await db.execute(select(models.Job).where(models.Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Get candidate profile
    result = await db.execute(
        select(models.CandidateProfile).where(
            models.CandidateProfile.user_id == current_user.id
        )
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Parse job requirements into individual skills
    job_skills = [
        s.strip().lower()
        for s in job.requirements.replace(",", " ").split()
        if len(s.strip()) > 1
    ]

    # Get candidate skills
    candidate_skills = [s.lower() for s in (profile.skills or [])]

    # Find matching and missing skills
    matching = [s for s in job_skills if any(s in cs or cs in s for cs in candidate_skills)]
    missing = [s for s in job_skills if not any(s in cs or cs in s for cs in candidate_skills)]

    # Compute match score
    match_score = 0.0
    if job.embedding is not None and profile.embedding is not None:
        import numpy as np
        job_vec = np.array(job.embedding)
        cand_vec = np.array(profile.embedding)
        match_score = float(np.dot(job_vec, cand_vec) / (np.linalg.norm(job_vec) * np.linalg.norm(cand_vec)))

    return SkillGapResponse(
        missing_skills=list(set(missing)),
        matching_skills=list(set(matching)),
        match_score=round(match_score, 4),
    )