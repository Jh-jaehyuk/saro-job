"""Pydantic v2 schemas for User auth endpoints.

fastapi-users 베이스 스키마를 상속받아 `org_id`만 추가로 노출한다. `org_id`는
가입 직후 `on_after_register` 훅에서 채워지므로 응답에서는 optional.
"""

import uuid

from fastapi_users import schemas


class UserRead(schemas.BaseUser[uuid.UUID]):
    org_id: uuid.UUID | None = None


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass
