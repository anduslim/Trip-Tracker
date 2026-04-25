.PHONY: install install-backend install-frontend migrate seed backend frontend dev test test-backend test-frontend lint fmt clean

PY := backend/.venv/bin/python
PIP := backend/.venv/bin/pip
ALEMBIC := backend/.venv/bin/alembic
PYTEST := backend/.venv/bin/pytest
UVICORN := backend/.venv/bin/uvicorn

install: install-backend install-frontend

install-backend:
	python3 -m venv backend/.venv
	$(PIP) install --upgrade pip
	$(PIP) install -e "backend[dev]"

install-frontend:
	cd frontend && npm install

migrate:
	cd backend && ../$(ALEMBIC) upgrade head

migration:
	cd backend && ../$(ALEMBIC) revision --autogenerate -m "$(m)"

seed:
	cd backend && ../$(PY) -m app.seeds.seed_dev

backend:
	cd backend && ../$(UVICORN) app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

dev:
	@echo "Run 'make backend' and 'make frontend' in separate terminals."

test: test-backend test-frontend

test-backend:
	cd backend && ../$(PYTEST) -q

test-frontend:
	cd frontend && npm test -- --run

lint:
	cd backend && ../backend/.venv/bin/ruff check app tests
	cd frontend && npm run lint

fmt:
	cd backend && ../backend/.venv/bin/ruff format app tests
	cd frontend && npm run fmt

clean:
	rm -rf backend/.venv backend/dev.db backend/test.db
	rm -rf frontend/node_modules frontend/dist
