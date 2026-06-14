# Skillio

An AI-powered job board that matches candidates to jobs using semantic embeddings rather than keyword search. Recruiters post jobs and review ranked applicants; candidates upload their resume and receive personalized recommendations based on cosine similarity between their profile and job descriptions.

**Live demo:** https://skillio-two.vercel.app

---

## Features

### Candidate
- Upload a PDF resume -- Gemini 2.5 Flash extracts skills, experience, and education into structured JSON
- Receive job recommendations ranked by semantic match score using sentence embeddings and pgvector
- AI-generated cover letters tailored to each job description on Apply
- Skill gap analysis showing which required skills you have and which to develop
- Track application status across all applied jobs

### Recruiter
- Post job listings with descriptions and requirements
- View applicants ranked by match score against the job embedding
- Access candidate resumes directly
- Update application status (Applied, Reviewed, Rejected, Offered)
- Close and reactivate job postings

### Platform
- JWT authentication with role-based access control (candidate vs recruiter)
- Rate limiting on auth and upload endpoints
- Search and filter jobs by title, location, and type
- Pagination on job listings
- 16 integration tests covering auth, jobs, and applications

---

## Tech Stack

**Backend**
- FastAPI, SQLAlchemy (async), PostgreSQL, pgvector
- sentence-transformers (`all-MiniLM-L6-v2`) for 384-dim embeddings
- Google Gemini 2.5 Flash for resume parsing and cover letter generation
- Supabase Storage for resume PDFs
- slowapi for rate limiting
- pytest + HTTPX for integration tests
- Docker + docker-compose

**Frontend**
- Next.js 14, TypeScript, Tailwind CSS
- Zustand for auth state
- Axios for API calls

**Infrastructure**
- Backend deployed on Railway
- Frontend deployed on Vercel
- PostgreSQL with pgvector on Railway

---

## How the Recommendation Engine Works

1. When a candidate uploads their resume, pdfplumber extracts the raw text
2. Gemini parses the text into structured JSON (skills, experience, education)
3. The candidate's profile text is encoded into a 384-dimensional vector using `all-MiniLM-L6-v2`
4. Job postings are similarly encoded when created
5. The `/recommendations` endpoint runs a pgvector cosine similarity query, ranking all active jobs by distance to the candidate's embedding
6. Results are returned sorted by similarity score with match percentage

---

## Running Locally

### Prerequisites
- Docker and docker-compose
- Node.js 18+
- Supabase account (for resume storage)
- Google AI Studio API key (for Gemini)

### Backend

```bash
# Clone the repo
git clone https://github.com/romashaguin-grad/skillio.git
cd skillio

# Create environment file
cp backend/.env.example backend/.env
# Fill in your keys in backend/.env

# Start backend and database
docker compose up --build
```

API docs available at `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install

# Create environment file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api" > .env.local

npm run dev
```

Frontend available at `http://localhost:3000`

### Running Tests

```bash
docker compose exec backend python -m pytest tests/ -v
```

---

## Project Structure

```
skillio/
├── backend/
│   ├── routers/          # Auth, jobs, applications, candidates, recommendations
│   ├── services/         # Embedding, resume parsing, cover letter, storage
│   ├── tests/            # Integration tests (pytest + HTTPX)
│   ├── models.py         # SQLAlchemy models
│   ├── main.py           # FastAPI app
│   └── Dockerfile
├── frontend/
│   └── src/app/
│       ├── dashboard/    # Candidate dashboard
│       ├── recruiter/    # Recruiter dashboard
│       ├── login/
│       └── register/
├── docker-compose.yml
└── railway.json
```

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (asyncpg) |
| `SECRET_KEY` | JWT signing key |
| `GEMINI_API_KEY` | Google AI Studio API key |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase anon key |

### Frontend (`frontend/.env.local`)

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL |
