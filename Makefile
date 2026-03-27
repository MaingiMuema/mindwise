backend-install:
	cd backend && python -m pip install -e .[dev]

backend-dev:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

worker:
	cd backend && celery -A app.core.celery_app.celery_app worker --loglevel=info

frontend-dev:
	cd frontend && npm install && npm run dev

migrate:
	cd backend && alembic upgrade head

test:
	cd backend && python -m pytest -q
