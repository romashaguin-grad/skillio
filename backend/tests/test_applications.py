import pytest
from httpx import AsyncClient


async def setup_recruiter_and_job(client: AsyncClient):
    res = await client.post("/api/auth/register", json={
        "email": "recruiter@test.com",
        "password": "testpassword123",
        "full_name": "Test Recruiter",
        "role": "recruiter"
    })
    token = res.json()["access_token"]
    job = await client.post("/api/jobs/", json={
        "title": "Backend Engineer",
        "company": "Test Corp",
        "location": "Remote",
        "description": "Build APIs with FastAPI and PostgreSQL.",
        "requirements": "Python, FastAPI, PostgreSQL",
        "salary_range": "$100k - $130k",
        "job_type": "Full-time"
    }, headers={"Authorization": f"Bearer {token}"})
    return token, job.json()["id"]


async def setup_candidate(client: AsyncClient):
    res = await client.post("/api/auth/register", json={
        "email": "candidate@test.com",
        "password": "testpassword123",
        "full_name": "Test Candidate",
        "role": "candidate"
    })
    return res.json()["access_token"]


async def test_apply_to_job(client: AsyncClient):
    recruiter_token, job_id = await setup_recruiter_and_job(client)
    candidate_token = await setup_candidate(client)

    response = await client.post("/api/applications/", json={
        "job_id": job_id,
        "cover_note": "I am very interested."
    }, headers={"Authorization": f"Bearer {candidate_token}"})
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "applied"
    assert data["cover_note"] == "I am very interested."


async def test_apply_twice_fails(client: AsyncClient):
    recruiter_token, job_id = await setup_recruiter_and_job(client)
    candidate_token = await setup_candidate(client)

    await client.post("/api/applications/", json={
        "job_id": job_id,
        "cover_note": "First apply."
    }, headers={"Authorization": f"Bearer {candidate_token}"})

    response = await client.post("/api/applications/", json={
        "job_id": job_id,
        "cover_note": "Second apply."
    }, headers={"Authorization": f"Bearer {candidate_token}"})
    assert response.status_code == 400
    assert "Already applied" in response.json()["detail"]


async def test_my_applications(client: AsyncClient):
    recruiter_token, job_id = await setup_recruiter_and_job(client)
    candidate_token = await setup_candidate(client)

    await client.post("/api/applications/", json={
        "job_id": job_id,
        "cover_note": "Interested."
    }, headers={"Authorization": f"Bearer {candidate_token}"})

    response = await client.get(
        "/api/applications/my-applications",
        headers={"Authorization": f"Bearer {candidate_token}"}
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["job_title"] == "Backend Engineer"


async def test_update_application_status(client: AsyncClient):
    recruiter_token, job_id = await setup_recruiter_and_job(client)
    candidate_token = await setup_candidate(client)

    app = await client.post("/api/applications/", json={
        "job_id": job_id,
        "cover_note": "Interested."
    }, headers={"Authorization": f"Bearer {candidate_token}"})
    app_id = app.json()["id"]

    response = await client.patch(
        f"/api/applications/{app_id}/status",
        json={"status": "reviewed"},
        headers={"Authorization": f"Bearer {recruiter_token}"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "reviewed"


async def test_recruiter_cannot_apply(client: AsyncClient):
    recruiter_token, job_id = await setup_recruiter_and_job(client)

    response = await client.post("/api/applications/", json={
        "job_id": job_id,
        "cover_note": "I want to apply."
    }, headers={"Authorization": f"Bearer {recruiter_token}"})
    assert response.status_code == 403