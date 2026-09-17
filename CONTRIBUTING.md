# Contributing

1. Create a branch from `main`.
2. Copy `.env.example` to `.env` and run `docker compose up --build`.
3. Run `ruff check app scripts tests` and `pytest` before opening a pull request.
4. Include an Alembic migration for every schema change.
5. Never commit Kaggle credentials, `.env`, or full generated embedding artifacts.
