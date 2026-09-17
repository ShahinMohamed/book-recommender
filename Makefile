.PHONY: dev up down logs test lint ingest-full

dev:
	uvicorn app.main:app --reload

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f web

test:
	pytest -q

lint:
	ruff check app scripts tests

ingest-full:
	docker compose run --rm --build -v "$${DATASET_PATH}:/imports/BooksDatasetClean.csv:ro" -v "$${EMBEDDINGS_PATH}:/imports/semantic_embeddings.npy:ro" -v "$${EMBEDDINGS_METADATA_PATH}:/imports/semantic_embeddings_metadata.json:ro" seed --dataset /imports/BooksDatasetClean.csv --embeddings /imports/semantic_embeddings.npy --metadata /imports/semantic_embeddings_metadata.json
