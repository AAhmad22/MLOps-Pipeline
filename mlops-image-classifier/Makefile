.PHONY: install test lint serve train docker-build compose-up clean

install:
	pip install -r requirements-dev.txt

test:
	pytest -q

lint:
	ruff check src tests

serve:
	uvicorn src.app:app --reload --port 8000

train:
	python -m src.train --data-dir data --epochs 5 --out artifacts/model.pt

docker-build:
	docker build -t image-classifier:local .

compose-up:
	docker compose up --build

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache
