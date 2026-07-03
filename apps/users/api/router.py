from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.ext.asyncio import AsyncSession

from apps.auth.api.deps import get_current_user
from apps.auth.api.permissions import require_role
from apps.users.domain.roles import Role
from apps.users.models.user import User
from apps.users.schemas import UserRead, UserUpdate
from apps.users.service import UserService
from core.db import get_db

router = APIRouter(tags=["users"])


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get the current user",
    description="Return the profile of the authenticated user.",
)
async def read_me(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.get(
    "/users",
    response_model=Page[UserRead],
    summary="List users",
    description="Return a paginated list of all users. Admins only.",
)
async def list_users(
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(Role.ADMIN)),
):
    service = UserService(session)
    return await paginate(session, service.list_query())


@router.get(
    "/users/{user_id}",
    response_model=UserRead,
    summary="Get a user by ID",
    description="Return a single user by their ID. Admins only.",
)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(Role.ADMIN)),
):
    service = UserService(session)
    user = await service.get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.patch(
    "/users/{user_id}",
    response_model=UserRead,
    summary="Update a user",
    description=(
        "Partially update a user. A user may update their own profile; admins "
        "may update anyone. Role and activation changes require admin rights."
    ),
)
async def update_user(
    user_id: int,
    data: UserUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    is_admin = current_user.role == Role.ADMIN
    if not is_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    service = UserService(session)
    user = await service.get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    try:
        updated = await service.update(user, data, allow_privileged=is_admin)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return updated


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user",
    description="Permanently delete a user by ID. Admins only.",
)
async def delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(Role.ADMIN)),
):
    service = UserService(session)
    user = await service.get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await service.delete(user)
