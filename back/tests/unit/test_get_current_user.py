import pytest
from datetime import timedelta

from fastapi import HTTPException
from jose import jwt

from app.auth import create_access_token, get_current_user
from app.config import settings


async def test_get_current_user_sub_none(test_db):
    """JWT に sub が含まれない場合は 401 を返す"""
    # sub なしのトークンを手動で生成
    from datetime import datetime, timezone

    payload = {
        "exp": datetime.now(timezone.utc) + timedelta(minutes=60),
        "data": "no-sub-here",
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")

    async with test_db() as db:
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token, db=db)
        assert exc_info.value.status_code == 401


async def test_get_current_user_user_not_found(test_db):
    """JWT の sub に存在しないユーザーIDが入っている場合は 401 を返す"""
    token = create_access_token({"sub": "99999"})

    async with test_db() as db:
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token, db=db)
        assert exc_info.value.status_code == 401
