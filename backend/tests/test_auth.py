import pytest
from app.services.auth import hash_password, verify_password, create_access_token, decode_token


def test_hash_and_verify_password():
    hashed = hash_password("mysecret")
    assert verify_password("mysecret", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_create_and_decode_token():
    token = create_access_token(data={"sub": "user@test.com", "role": "admin"})
    payload = decode_token(token)
    assert payload["sub"] == "user@test.com"
    assert payload["role"] == "admin"


def test_decode_invalid_token():
    payload = decode_token("invalid.token.here")
    assert payload is None
