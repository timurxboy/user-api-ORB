from typing import ClassVar

from sqladmin import ModelView

from apps.auth.models.refresh_token import RefreshToken


class RefreshTokenAdmin(ModelView, model=RefreshToken):
    name = "Refresh Token"
    name_plural = "Refresh Tokens"
    icon = "fa-solid fa-key"

    column_list: ClassVar = [
        RefreshToken.id,
        RefreshToken.user_id,
        RefreshToken.token,
        RefreshToken.expires_at,
    ]
    column_sortable_list: ClassVar = [
        RefreshToken.id,
        RefreshToken.user_id,
        RefreshToken.expires_at,
    ]
    column_searchable_list: ClassVar = [RefreshToken.token]

    # Tokens are issued by the auth flow, not created by hand.
    can_create = False
    can_edit = False
