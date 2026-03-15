import secrets
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, TokenResponse
from app.services.auth import hash_password, verify_password, create_access_token
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


# ---------- Register ----------

@router.post("/register", response_model=UserResponse, status_code=201)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


# ---------- Login ----------

@router.post("/login", response_model=TokenResponse)
async def login(login_in: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == login_in.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(login_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Account deactivated"
        )
    user.last_login = datetime.now(timezone.utc)
    await db.commit()
    access_token = create_access_token(data={"sub": user.email, "role": user.role.value})
    refresh_token = create_access_token(data={"sub": user.email, "type": "refresh"})
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        must_change_password=user.must_change_password,
    )


# ---------- Me ----------

@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return UserResponse.model_validate(user)


# ---------- Change Password ----------

@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(body.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    user.hashed_password = hash_password(body.new_password)
    user.must_change_password = False
    await db.commit()
    return {"message": "Password changed"}


# ---------- Forgot Password ----------

@router.post("/forgot-password")
async def forgot_password(
    body: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    response = {"message": "If the email exists, a reset link has been sent"}
    if not user:
        return response
    token = secrets.token_urlsafe(32)
    user.password_reset_token = token
    user.password_reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
    await db.commit()
    # In dev mode, return the token directly
    if settings.app_env == "development":
        response["reset_token"] = token
    return response


# ---------- Reset Password ----------

@router.post("/reset-password")
async def reset_password(
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.password_reset_token == body.token)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    if user.password_reset_expires is None or user.password_reset_expires < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    user.hashed_password = hash_password(body.new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    user.must_change_password = False
    await db.commit()
    return {"message": "Password reset successful"}


# ---------- OIDC Login ----------

@router.get("/oidc/login")
async def oidc_login():
    if not settings.oidc_enabled:
        raise HTTPException(status_code=404, detail="OIDC is not enabled")
    async with httpx.AsyncClient() as client:
        resp = await client.get(settings.oidc_discovery_url)
        resp.raise_for_status()
        discovery = resp.json()
    authorization_endpoint = discovery["authorization_endpoint"]
    params = (
        f"?client_id={settings.oidc_client_id}"
        f"&redirect_uri={settings.oidc_redirect_uri}"
        f"&response_type=code"
        f"&scope=openid email profile"
    )
    return {"authorization_url": authorization_endpoint + params}


# ---------- OIDC Callback ----------

@router.get("/oidc/callback", response_model=TokenResponse)
async def oidc_callback(
    code: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    if not settings.oidc_enabled:
        raise HTTPException(status_code=404, detail="OIDC is not enabled")

    # Fetch discovery document
    async with httpx.AsyncClient() as client:
        resp = await client.get(settings.oidc_discovery_url)
        resp.raise_for_status()
        discovery = resp.json()

        # Exchange code for tokens
        token_resp = await client.post(
            discovery["token_endpoint"],
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.oidc_redirect_uri,
                "client_id": settings.oidc_client_id,
                "client_secret": settings.oidc_client_secret,
            },
        )
        token_resp.raise_for_status()
        token_data = token_resp.json()

        # Get user info
        userinfo_resp = await client.get(
            discovery["userinfo_endpoint"],
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
        userinfo_resp.raise_for_status()
        userinfo = userinfo_resp.json()

    email = userinfo.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="OIDC provider did not return an email")
    full_name = userinfo.get("name") or userinfo.get("preferred_username") or email

    # Look up or create user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user:
        user.last_login = datetime.now(timezone.utc)
    else:
        user = User(
            email=email,
            hashed_password="",  # No local password for OIDC users
            full_name=full_name,
            role=UserRole.SUBMITTER,
            must_change_password=False,
            last_login=datetime.now(timezone.utc),
        )
        db.add(user)
    await db.commit()
    await db.refresh(user)

    access_token = create_access_token(data={"sub": user.email, "role": user.role.value})
    refresh_token = create_access_token(data={"sub": user.email, "type": "refresh"})
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        must_change_password=user.must_change_password,
    )
