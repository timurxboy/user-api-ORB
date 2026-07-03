from datetime import timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.auth.models.refresh_token import RefreshToken
from apps.auth.models.verification import VerificationCode
from apps.auth.utils.email import get_email_sender
from apps.auth.utils.jwt import create_access_token, create_refresh_token
from apps.auth.utils.verification import generate_verification_code
from apps.users.domain.roles import Role
from apps.users.models.user import User
from core.datetime import as_utc, utcnow
from core.settings import core_settings


class AuthService:
    """Authentication flows: signup, login, refresh, verification, logout."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ---- helpers ----

    async def _get_user_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def _issue_tokens(self, user: User) -> tuple[str, str]:
        access = create_access_token(subject=user.id, role=user.role)
        refresh_value = create_refresh_token()

        refresh = RefreshToken(
            token=refresh_value,
            user_id=user.id,
            expires_at=utcnow() + timedelta(days=core_settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        self.session.add(refresh)
        await self.session.flush()

        return access, refresh_value

    async def _create_verification_code(self, user: User) -> str:
        code = generate_verification_code()
        record = VerificationCode(
            user_id=user.id,
            code=code,
            expires_at=utcnow() + timedelta(minutes=core_settings.VERIFICATION_CODE_EXPIRE_MINUTES),
        )
        self.session.add(record)
        await self.session.flush()
        return code

    # ---- flows ----

    async def signup(
        self,
        *,
        email: str,
        password: str,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> User:
        """Register a new (unverified) user and send a verification code."""
        if await self._get_user_by_email(email):
            raise ValueError("Email already registered")

        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=Role.USER,
        )
        user.password = password

        self.session.add(user)
        await self.session.flush()

        code = await self._create_verification_code(user)

        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        # Delivery happens after commit so the code is guaranteed to exist.
        await get_email_sender().send_verification_code(email=email, code=code)

        return user

    async def login(self, *, email: str, password: str) -> tuple[str, str]:
        """Validate credentials and issue an access/refresh token pair."""
        user = await self._get_user_by_email(email)

        if not user or not user.verify_password(password):
            raise ValueError("Invalid credentials")
        if not user.is_active:
            raise ValueError("User account is deactivated")
        if not user.is_verified:
            raise ValueError("Email is not verified")

        access, refresh_value = await self._issue_tokens(user)

        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        return access, refresh_value

    async def refresh(self, refresh_token: str) -> str:
        """Exchange a valid refresh token for a fresh access token."""
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token == refresh_token)
        )
        token = result.scalar_one_or_none()

        if not token or as_utc(token.expires_at) < utcnow():
            raise ValueError("Invalid or expired refresh token")

        user = await self.session.get(User, token.user_id)
        if not user or not user.is_active:
            raise ValueError("User not found or deactivated")

        return create_access_token(subject=user.id, role=user.role)

    async def verify(self, *, email: str, code: str) -> None:
        """Confirm a verification code and mark the user as verified."""
        user = await self._get_user_by_email(email)
        if not user:
            raise ValueError("User not found")
        if user.is_verified:
            return

        result = await self.session.execute(
            select(VerificationCode)
            .where(
                VerificationCode.user_id == user.id,
                VerificationCode.code == code,
                VerificationCode.used.is_(False),
            )
            .order_by(VerificationCode.id.desc())
        )
        record = result.scalars().first()

        if not record or as_utc(record.expires_at) < utcnow():
            raise ValueError("Invalid or expired verification code")

        record.used = True
        user.is_verified = True

        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

    async def logout(self, refresh_token: str) -> None:
        """Revoke a refresh token."""
        await self.session.execute(delete(RefreshToken).where(RefreshToken.token == refresh_token))
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

    async def resend_verification_code(self, *, email: str) -> None:
        """Issue and deliver a fresh verification code (best-effort).

        The outcome is intentionally the same whether or not the email exists,
        to avoid leaking which addresses are registered.
        """
        user = await self._get_user_by_email(email)
        if not user or user.is_verified:
            return

        code = await self._create_verification_code(user)
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        await get_email_sender().send_verification_code(email=email, code=code)

    async def create_admin(self, *, email: str, password: str) -> User:
        """Create a verified admin user (used by the CLI)."""
        if await self._get_user_by_email(email):
            raise ValueError(f"User '{email}' already exists")

        user = User(email=email, role=Role.ADMIN, is_verified=True)
        user.password = password

        self.session.add(user)
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        return user
