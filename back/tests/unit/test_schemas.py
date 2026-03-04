import pytest
from pydantic import ValidationError

from app.schemas.review import ReviewCreate, ReviewResponse
from app.schemas.user import UserCreate, UserResponse
from app.schemas.sento import SentoResponse, SentoListResponse
from app.schemas.auth import LoginRequest, TokenResponse


# --- ReviewCreate ---

def test_review_create_valid_rating_1():
    r = ReviewCreate(rating=1)
    assert r.rating == 1
    assert r.comment is None


def test_review_create_valid_rating_5():
    r = ReviewCreate(rating=5, comment="最高の銭湯です")
    assert r.rating == 5
    assert r.comment == "最高の銭湯です"


def test_review_create_rating_too_low():
    with pytest.raises(ValidationError):
        ReviewCreate(rating=0)


def test_review_create_rating_too_high():
    with pytest.raises(ValidationError):
        ReviewCreate(rating=6)


def test_review_create_comment_too_long():
    with pytest.raises(ValidationError):
        ReviewCreate(rating=3, comment="a" * 1001)


def test_review_create_comment_max_length():
    r = ReviewCreate(rating=3, comment="a" * 1000)
    assert len(r.comment) == 1000


def test_review_create_missing_rating():
    with pytest.raises(ValidationError):
        ReviewCreate()


# --- UserCreate ---

def test_user_create_valid():
    u = UserCreate(username="testuser", email="test@example.com", password="password123")
    assert u.username == "testuser"
    assert u.email == "test@example.com"


def test_user_create_password_too_short():
    with pytest.raises(ValidationError):
        UserCreate(username="user", email="a@b.com", password="short")


def test_user_create_password_min_length():
    u = UserCreate(username="user", email="a@b.com", password="12345678")
    assert u.password == "12345678"


def test_user_create_invalid_email():
    with pytest.raises(ValidationError):
        UserCreate(username="user", email="not-email", password="password123")


def test_user_create_empty_username():
    with pytest.raises(ValidationError):
        UserCreate(username="", email="a@b.com", password="password123")


def test_user_create_username_too_long():
    with pytest.raises(ValidationError):
        UserCreate(username="a" * 51, email="a@b.com", password="password123")


def test_user_create_username_max_length():
    u = UserCreate(username="a" * 50, email="a@b.com", password="password123")
    assert len(u.username) == 50


# --- TokenResponse ---

def test_token_response_default_type():
    t = TokenResponse(access_token="some-token")
    assert t.token_type == "bearer"
    assert t.access_token == "some-token"


def test_token_response_custom_type():
    t = TokenResponse(access_token="tok", token_type="Bearer")
    assert t.token_type == "Bearer"


# --- LoginRequest ---

def test_login_request_valid():
    r = LoginRequest(email="user@example.com", password="mypassword")
    assert r.email == "user@example.com"


def test_login_request_invalid_email():
    with pytest.raises(ValidationError):
        LoginRequest(email="not-valid", password="mypassword")


# --- SentoListResponse ---

def test_sento_list_response_empty():
    resp = SentoListResponse(items=[], total=0, page=1, per_page=50)
    assert resp.items == []
    assert resp.total == 0
