from fastapi import Depends, HTTPException, status

from apps.auth.api.deps import get_current_user
from apps.users.domain.roles import Role
from apps.users.models.user import User


def require_role(*allowed_roles: Role):
    """Dependency factory enforcing that the current user has one of the roles."""

    async def checker(
        user: User = Depends(get_current_user),
    ) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return checker
