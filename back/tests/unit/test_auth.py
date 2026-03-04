import pytest
from datetime import timedelta

from jose import jwt, JWTError

from app.auth import create_access_token
from app.config import settings


def test_create_access_token_contains_sub():
    token = create_access_token({"sub": "42"})
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
    assert payload["sub"] == "42"


def test_create_access_token_has_exp():
    token = create_access_token({"sub": "1"})
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
    assert "exp" in payload


def test_create_access_token_with_custom_expires():
    token = create_access_token({"sub": "1"}, expires_delta=timedelta(minutes=1))
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
    assert payload["sub"] == "1"


def test_create_access_token_invalid_after_tamper():
    token = create_access_token({"sub": "1"})
    tampered = token + "x"
    with pytest.raises(JWTError):
        jwt.decode(tampered, settings.jwt_secret_key, algorithms=["HS256"])


def test_create_access_token_wrong_secret():
    token = create_access_token({"sub": "1"})
    with pytest.raises(JWTError):
        jwt.decode(token, "wrong-secret", algorithms=["HS256"])


def test_create_access_token_multiple_claims():
    token = create_access_token({"sub": "99", "role": "admin"})
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
    assert payload["sub"] == "99"
    assert payload["role"] == "admin"
