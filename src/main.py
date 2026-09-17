"""Compatibility entry point.

The former monolithic prototype was split into production modules under ``app``.
Start the website with ``uvicorn app.main:app``.
"""

from app.main import app


__all__ = ["app"]
