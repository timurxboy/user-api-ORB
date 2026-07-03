from enum import StrEnum


class Role(StrEnum):
    """User access roles.

    USER  - standard user with access to their own resources.
    ADMIN - elevated user with access to user-management endpoints.
    """

    USER = "user"
    ADMIN = "admin"
