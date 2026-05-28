"""fastapi-users 와이어링: UserManager, 인증 백엔드(쿠키+JWT), OAuth 클라이언트.

세션 정책: fastapi-users의 `SQLAlchemyUserDatabase`는 내부에서 `session.commit()`을
호출한다. 이는 우리 `get_session()`의 `session.begin()` 블록과 충돌하므로, 인증 흐름은
별도 의존성 `get_auth_session()`에서 트랜잭션 비개시 세션을 받아 쓴다 (AGENTS.md §7
"라우터 단위 트랜잭션" 원칙은 도메인 라우터에 적용; 인증은 라이브러리 위임).
"""

import uuid
from collections.abc import AsyncIterator
from typing import Annotated, Any

from fastapi import Depends
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    CookieTransport,
    JWTStrategy,
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from httpx_oauth.clients.google import GoogleOAuth2
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import AsyncSessionLocal
from app.models.organization import Organization
from app.models.user import User


async def get_auth_session() -> AsyncIterator[AsyncSession]:
    """Session for fastapi-users — no outer `begin()`, library commits itself."""
    async with AsyncSessionLocal() as session:
        yield session


async def get_user_db(
    session: Annotated[AsyncSession, Depends(get_auth_session)],
) -> AsyncIterator[SQLAlchemyUserDatabase[User, uuid.UUID]]:
    yield SQLAlchemyUserDatabase(session, User)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = get_settings().auth_secret_key
    verification_token_secret = get_settings().auth_secret_key

    async def on_after_register(self, user: User, request: Any = None) -> None:
        """가입 직후 1인 워크스페이스 조직을 생성하고 user.org_id를 채운다."""
        session = self.user_db.session  # type: ignore[attr-defined]
        org = Organization(name=f"{user.email}'s workspace")
        session.add(org)
        await session.flush()
        user.org_id = org.id
        session.add(user)
        await session.commit()
        await session.refresh(user)


async def get_user_manager(
    user_db: Annotated[SQLAlchemyUserDatabase[User, uuid.UUID], Depends(get_user_db)],
) -> AsyncIterator[UserManager]:
    yield UserManager(user_db)


cookie_transport = CookieTransport(
    cookie_name="sarojob_session",
    cookie_max_age=get_settings().auth_cookie_max_age,
    cookie_secure=get_settings().auth_cookie_secure,
    cookie_httponly=True,
    cookie_samesite="lax",
)


def get_jwt_strategy() -> JWTStrategy[User, uuid.UUID]:
    return JWTStrategy(
        secret=get_settings().auth_secret_key,
        lifetime_seconds=get_settings().auth_cookie_max_age,
    )


auth_backend = AuthenticationBackend(
    name="cookie",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)


fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)


def _make_google_oauth_client() -> GoogleOAuth2 | None:
    s = get_settings()
    if not s.google_oauth_client_id or not s.google_oauth_client_secret:
        return None
    return GoogleOAuth2(s.google_oauth_client_id, s.google_oauth_client_secret)


google_oauth_client = _make_google_oauth_client()
