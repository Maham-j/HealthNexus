.PHONY: install run dev test lint clean check-neo4j poetry-install poetry-run poetry-dev poetry-test

VENV := venv

ifeq ($(OS),Windows_NT)
	PYTHON := $(VENV)\Scripts\python.exe
	PIP := $(VENV)\Scripts\pip.exe
	UVICORN := $(VENV)\Scripts\uvicorn.exe
	PYTEST := $(VENV)\Scripts\pytest.exe
	ENV_COPY := if not exist .env copy .env.example .env
else
	PYTHON := $(VENV)/bin/python
	PIP := $(VENV)/bin/pip
	UVICORN := $(VENV)/bin/uvicorn
	PYTEST := $(VENV)/bin/pytest
	ENV_COPY := cp -n .env.example .env || true
endif

# ---- pip + venv workflow ----

install:
	python -m venv $(VENV)
	$(PYTHON) -m pip install --upgrade pip
	$(PIP) install -r requirements.txt
	$(ENV_COPY)
	@echo "Now edit .env with your real Neo4j + LLM credentials."

run:
	$(UVICORN) app.main:app --host 0.0.0.0 --port 8000

dev:
	$(UVICORN) app.main:app --reload --host 0.0.0.0 --port 8000

test:
	$(PYTEST) tests/ -v

check-neo4j:
	$(PYTHON) scripts/check_neo4j_connection.py

clean:
	@echo "run manually on windows: rd /s /q venv __pycache__"

# ---- Poetry workflow (alternative to pip+venv above) ----
# Requires Poetry installed: https://python-poetry.org/docs/#installation

poetry-install:
	poetry install
	$(ENV_COPY)
	@echo "Now edit .env with your real Neo4j + LLM credentials."

poetry-run:
	poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000

poetry-dev:
	poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

poetry-test:
	poetry run pytest tests/ -v
