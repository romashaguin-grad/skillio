import pytest
from httpx import AsyncClient


async def get_recruiter_token(client: AsyncClient) -> str:
    res = await client.post("/api/auth/register", json={
        "email": "recruiter@test.com",
        "password": "testpassword123",
        "full_name": "Test Recruiter",
        "role": "recruiter"
    })
    return res.json()["access_token"]


async def get_candidate_token(client: AsyncClient) -> str:
    res = await client.post("/api/auth/register", json={
        "email": "candidate@test.com",
        "password": "testpassword123",
        "full_name": "Test Candidate",
        "role": "candidate"
    })
    return res.json()["access_token"]


async def test_create_job(client: AsyncClient):
    token = await get_recruiter_token(client)
    response = await client.post("/api/jobs/", json={
        "title": "Backend Engineer",
        "company": "Test Corp",
        "location": "Remote",
        "description": "Build APIs with FastAPI and PostgreSQL.",
        "requirements": "Python, FastAPI, PostgreSQL",
        "salary_range": "$100k - $130k",
        "job_type": "Full-time"
    }, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Backend Engineer"
    assert data["company"] == "Test Corp"


async def test_create_job_as_candidate_fails(client: AsyncClient):
    token = await get_candidate_token(client)
    response = await client.post("/api/jobs/", json={
        "title": "Backend Engineer",
        "company": "Test Corp",
        "location": "Remote",
        "description": "Build APIs.",
        "requirements": "Python",
        "salary_range": "$100k",
        "job_type": "Full-time"
    }, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


async def test_list_jobs(client: AsyncClient):
    token = await get_recruiter_token(client)
    await client.post("/api/jobs/", json={
        "title": "ML Engineer",
        "company": "AI Corp",
        "location": "Remote",
        "description": "Build ML models.",
        "requirements": "Python, PyTorch",
        "salary_range": "$120k",
        "job_type": "Full-time"
    }, headers={"Authorization": f"Bearer {token}"})
    response = await client.get("/api/jobs/")
    assert response.status_code == 200
    assert len(response.json()) >= 1


async def test_toggle_job(client: AsyncClient):
    token = await get_recruiter_token(client)
    create = await client.post("/api/jobs/", json={
        "title": "DevOps Engineer",
        "company": "Ops Corp",
        "location": "Remote",
        "description": "Manage infrastructure.",
        "requirements": "Docker, Kubernetes",
        "salary_range": "$110k",
        "job_type": "Full-time"
    }, headers={"Authorization": f"Bearer {token}"})
    job_id = create.json()["id"]

    response = await client.patch(
        f"/api/jobs/{job_id}/toggle",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["is_active"] == False


async def test_create_job_unauthenticated(client: AsyncClient):
    response = await client.post("/api/jobs/", json={
        "title": "Backend Engineer",
        "company": "Test Corp",
        "location": "Remote",
        "description": "Build APIs.",
        "requirements": "Python",
        "salary_range": "$100k",
        "job_type": "Full-time"
    })
    assert response.status_code == 401