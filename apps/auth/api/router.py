from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.auth.schemas import (
    EmailRequest,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    RefreshRequest,
    SignupRequest,
    TokenResponse,
    VerifyRequest,
)
from apps.auth.service.auth import AuthService
from apps.users.schemas import UserRead
from core.db import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/signup",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description=(
        "Create a new account with an email and password (name is optional). "
        "The user starts unverified and a verification code is sent to the "
        "provided email (printed to the log in dev)."
    ),
)
async def signup(
    data: SignupRequest,
    session: AsyncSession = Depends(get_db),
):
    service = AuthService(session)
    try:
        user = await service.signup(
            email=data.email,
            password=data.password,
            first_name=data.first_name,
            last_name=data.last_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return user


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Log in and obtain tokens",
    description="Authenticate with email and password and receive an access "
    "and refresh token pair. Requires a verified account.",
)
async def login(
    data: LoginRequest,
    session: AsyncSession = Depends(get_db),
):
    service = AuthService(session)
    try:
        access, refresh = await service.login(
            email=data.email,
            password=data.password,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e

    return LoginResponse(access_token=access, refresh_token=refresh)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh the access token",
    description="Exchange a valid refresh token for a new access token.",
)
async def refresh(
    data: RefreshRequest,
    session: AsyncSession = Depends(get_db),
):
    service = AuthService(session)
    try:
        access = await service.refresh(data.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e

    return TokenResponse(access_token=access)


@router.post(
    "/verify",
    response_model=MessageResponse,
    summary="Verify an email address",
    description="Confirm ownership of an email using the code sent at signup. "
    "On success the account becomes verified.",
)
async def verify(
    data: VerifyRequest,
    session: AsyncSession = Depends(get_db),
):
    service = AuthService(session)
    try:
        await service.verify(email=data.email, code=data.code)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return MessageResponse(message="Email verified successfully")


@router.post(
    "/resend-code",
    response_model=MessageResponse,
    summary="Resend a verification code",
    description="Issue and send a new verification code for an unverified "
    "account. Always returns success to avoid leaking registered emails.",
)
async def resend_code(
    data: EmailRequest,
    session: AsyncSession = Depends(get_db),
):
    service = AuthService(session)
    await service.resend_verification_code(email=data.email)
    return MessageResponse(message="If the account exists, a code has been sent")


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Log out",
    description="Revoke the given refresh token so it can no longer be used.",
)
async def logout(
    data: RefreshRequest,
    session: AsyncSession = Depends(get_db),
):
    service = AuthService(session)
    await service.logout(data.refresh_token)
    return MessageResponse(message="Logged out")
