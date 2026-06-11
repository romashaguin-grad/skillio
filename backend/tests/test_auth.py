import pytest
from httpx import AsyncClient


async def test_register_candidate(client: AsyncClient):
    response = await client.post("/api/auth/register", json={
        "email": "candidate@test.com",
        "password": "testpassword123",
        "full_name": "Test Candidate",
        "role": "candidate"
    })
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "candidate"
    assert data["full_name"] == "Test Candidate"


async def test_register_recruiter(client: AsyncClient):
    response = await client.post("/api/auth/register", json={
        "email": "recruiter@test.com",
        "password": "testpassword123",
        "full_name": "Test Recruiter",
        "role": "recruiter"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "recruiter"


async def test_register_duplicate_email(client: AsyncClient):
    await client.post("/api/auth/register", json={
        "email": "duplicate@test.com",
        "password": "testpassword123",
        "full_name": "User One",
        "role": "candidate"
    })
    response = await client.post("/api/auth/register", json={
        "email": "duplicate@test.com",
        "password": "testpassword123",
        "full_name": "User Two",
        "role": "candidate"
    })
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


async def test_login_success(client: AsyncClient):
    await client.post("/api/auth/register", json={
        "email": "login@test.com",
        "password": "testpassword123",
        "full_name": "Login User",
        "role": "candidate"
    })
    response = await client.post("/api/auth/login", data={
        "username": "login@test.com",
        "password": "testpassword123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_login_wrong_password(client: AsyncClient):
    await client.post("/api/auth/register", json={
        "email": "wrong@test.com",
        "password": "testpassword123",
        "full_name": "Wrong User",
        "role": "candidate"
    })
    response = await client.post("/api/auth/login", data={
        "username": "wrong@test.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401


async def test_get_me(client: AsyncClient):
    reg = await client.post("/api/auth/register", json={
        "email": "me@test.com",
        "password": "testpassword123",
        "full_name": "Me User",
        "role": "candidate"
    })
    token = reg.json()["access_token"]
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "me@test.com"