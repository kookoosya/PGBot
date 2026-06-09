.PHONY: check lint test backend-lint backend-test backend-audit frontend-lint frontend-build install-dev

install-dev:
	cd backend && pip install -r requirements-dev.txt
	cd frontend && npm install

backend-lint:
	cd backend && ruff check app tests scripts
	cd backend && ruff format --check app tests scripts

backend-test:
	cd backend && pytest -q

backend-audit:
	cd backend && pip-audit -r requirements.txt

frontend-lint:
	cd frontend && npm run lint

frontend-build:
	cd frontend && npm run build

lint: backend-lint frontend-lint

test: backend-test

check: backend-lint backend-test backend-audit frontend-lint frontend-build
