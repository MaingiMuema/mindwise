# MindWise

MindWise is a Python-first AI video generation platform for long-form explainer content. It accepts prompts and structured lesson requests, plans a scene-by-scene video specification, renders each scene independently, and composes resumable exports for educational topics such as mathematics, physics, finance, computer science, AI/ML, engineering, and abstract technical explainers.

This repository now includes:

- A FastAPI backend with modular services for auth, planning, layout safety, math validation, asset generation, TTS, subtitles, Manim rendering, FFmpeg composition, and Celery workers.
- SQLAlchemy models and Alembic migrations for users, sessions, projects, jobs, scenes, assets, render attempts, outputs, logs, and usage.
- A React + TypeScript + Vite frontend for project creation, job launch, scene inspection, render monitoring, retry, rerender, and export download.
- Tests for planning, layout overflow, math validation, provider fallback, TTS fallback, Stable Horde image persistence, FFmpeg manifest creation, retry flows, and API project/job creation.

## Architecture

### Backend

`backend/app/api`
- REST endpoints for auth, projects, jobs, logs, asset retrieval, exports, health, and readiness.

`backend/app/models`
- SQLAlchemy 2.0 models for the core production entities.

`backend/app/services/planning`
- Structured scene planning using `VideoSpec`, `SceneSpecModel`, `VisualElement`, `AnimationSpec`, `NarrationSpec`, and `AssetSpec`.

`backend/app/services/layout`
- Viewport-safe layout estimation, font scaling heuristics, overflow detection, and scene splitting.

`backend/app/services/math`
- SymPy-based expression validation, equivalence checks, and LaTeX conversion.

`backend/app/services/rendering`
- Manim template renderers driven by structured specs rather than raw LLM-generated animation code.

`backend/app/services/images`
- Stable Horde adapter with polling, persistence, and cache-by-prompt behavior.

`backend/app/services/tts`
- Provider abstraction with Piper support and a dummy fallback for development/test environments.

`backend/app/services/composition`
- FFmpeg scene muxing and final concat composition.

`backend/app/services/jobs`
- Scene-by-scene orchestration, resume support, retry support, logging, and output persistence.

`backend/app/workers`
- Celery tasks for full job execution and single-scene rerender flows.

### Frontend

`frontend/src`
- Dashboard for projects.
- New-project flow.
- Google OAuth callback handling.
- Project detail page with job launch.
- Job monitor with polling, logs, scene rerender, retry, and export download.

## Scene Pipeline

1. Create a project from a prompt or lesson request.
2. Create a render job for a target duration and style.
3. Generate a structured `RenderJobPlan`.
4. Persist scene specs individually in the database.
5. Resolve assets scene-by-scene.
6. Generate narration audio per scene.
7. Generate scene subtitles.
8. Render each scene independently with Manim.
9. Mux scene video, audio, and subtitles with FFmpeg.
10. Concatenate successful scene clips into the final export.

The design is resumable because completed scene clips are stored individually and failed scenes can be retried without regenerating the full video.

## Stack

- Backend: FastAPI, SQLAlchemy, Pydantic, Alembic
- Queue: Celery + Redis
- Database: MySQL in production, SQLite-friendly for tests/dev bootstrap
- Math: SymPy
- Rendering: Manim
- Composition: FFmpeg
- TTS: Piper-ready abstraction with dummy fallback
- Image fallback: Stable Horde
- Frontend: React, TypeScript, Vite, React Query, React Router
- Auth: Google OAuth + signed JWT-style tokens

## Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- Redis
- MySQL
- FFmpeg on PATH
- Manim on PATH
- Optional: Piper with a local model file

### Backend

1. Copy [backend/.env.example](/Users/Lenovo/Desktop/Projects/mindwise/backend/.env.example) to `backend/.env`.
2. Fill in real values for:
   - `DATABASE_URL`
   - `JWT_SECRET_KEY`
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `GOOGLE_REDIRECT_URI`
   - optional LLM and Stable Horde keys
3. Install dependencies:

```bash
cd backend
python -m pip install -e .[dev,render]
```

4. Run migrations:

```bash
alembic upgrade head
```

5. Start the API:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

6. Start the worker in another terminal:

```bash
celery -A app.core.celery_app.celery_app worker --loglevel=info
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend expects the backend at `http://localhost:8000/api/v1` by default. Override with `VITE_API_BASE_URL` if needed.

### Windows-Friendly Scripts

- [backend/scripts/dev.ps1](/Users/Lenovo/Desktop/Projects/mindwise/backend/scripts/dev.ps1)
- [backend/scripts/worker.ps1](/Users/Lenovo/Desktop/Projects/mindwise/backend/scripts/worker.ps1)
- [backend/scripts/migrate.ps1](/Users/Lenovo/Desktop/Projects/mindwise/backend/scripts/migrate.ps1)

## Developer Commands

From repo root:

```bash
make backend-install
make backend-dev
make worker
make frontend-dev
make migrate
make test
```

## Example Inputs

See [docs/demo-prompts.md](/Users/Lenovo/Desktop/Projects/mindwise/docs/demo-prompts.md) and [video_presets.json](/Users/Lenovo/Desktop/Projects/mindwise/backend/app/templates/video_presets.json) for starter prompts and preset durations/styles.

## API Surface

Implemented endpoints include:

- `GET /api/v1/health`
- `GET /api/v1/system/readiness`
- `GET /api/v1/auth/google/login`
- `POST /api/v1/auth/google/callback`
- `POST /api/v1/auth/refresh`
- `GET /api/v1/auth/me`
- `GET /api/v1/projects`
- `POST /api/v1/projects`
- `GET /api/v1/projects/{project_id}`
- `PATCH /api/v1/projects/{project_id}`
- `POST /api/v1/projects/{project_id}/jobs`
- `GET /api/v1/jobs/{job_id}`
- `GET /api/v1/jobs/{job_id}/scenes`
- `GET /api/v1/jobs/{job_id}/logs`
- `POST /api/v1/jobs/{job_id}/retry`
- `POST /api/v1/jobs/{job_id}/scenes/{scene_id}/rerender`
- `GET /api/v1/assets/{asset_id}`
- `GET /api/v1/exports/{job_id}`

## Notes

- The backend intentionally uses structured scene specs and fixed render templates instead of raw LLM animation code.
- Layout safety is enforced before rendering and can split dense scenes into paginated parts.
- The current repository does not commit secrets. The existing local `backend/.env` was left untouched.
- The test suite is included, but `pytest` was not installed in the current machine image during this run, so runtime test execution was not completed here.
- The frontend production build was verified with `npm run build`.
