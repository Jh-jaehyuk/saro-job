"""FastAPI application entrypoint."""

from fastapi import FastAPI

from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.routers.auth import router as auth_router
from app.routers.health import router as health_router
from app.routers.jds import router as jds_router
from app.routers.matches import router as matches_router
from app.routers.progress import router as progress_router
from app.routers.resumes import router as resumes_router

configure_logging()

app = FastAPI(title="saro-job-api")

register_exception_handlers(app)
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(jds_router)
app.include_router(resumes_router)
app.include_router(matches_router)
app.include_router(progress_router)
