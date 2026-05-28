"""FastAPI application entrypoint."""

from fastapi import FastAPI

from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.routers.auth import router as auth_router
from app.routers.health import router as health_router

configure_logging()

app = FastAPI(title="saro-job-api")

register_exception_handlers(app)
app.include_router(health_router)
app.include_router(auth_router)
