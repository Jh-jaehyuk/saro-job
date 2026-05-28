"""Auth 라우터 — fastapi-users 제공 라우터를 묶어 등록한다.

엔드포인트:
- POST /auth/cookie/login, /auth/cookie/logout
- POST /auth/register
- GET  /auth/google/authorize, /auth/google/callback (OAuth 키가 설정된 경우만)
- GET  /users/me, PATCH /users/me
"""

from fastapi import APIRouter

from app.core.auth import (
    auth_backend,
    fastapi_users,
    google_oauth_client,
)
from app.core.config import get_settings
from app.schemas.user import UserCreate, UserRead, UserUpdate

router = APIRouter()

router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/cookie",
    tags=["auth"],
)
router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

if google_oauth_client is not None:
    router.include_router(
        fastapi_users.get_oauth_router(
            google_oauth_client,
            auth_backend,
            get_settings().auth_secret_key,
            redirect_url=get_settings().google_oauth_redirect_url,
            associate_by_email=True,
        ),
        prefix="/auth/google",
        tags=["auth"],
    )
