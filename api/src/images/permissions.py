from rest_framework import permissions
from django.http import HttpRequest
from django.views import View
from images.tokens import expiring_image_token_generator


class IsObjectOwner(permissions.BasePermission):
    """
    Generic Permission that allows to check if request.user
    is object owner or not. Object owner field is determined
    by class attribute 'object_owner_field'
    """

    object_owner_field = "owner"

    def has_object_permission(
        self, request: HttpRequest, view: View, obj: object
    ) -> bool:
        return getattr(obj, self.object_owner_field) == request.user


class IsImageOwner(IsObjectOwner):
    """
    Permission used to check if request.user is
    Image owner
    """

    object_owner_field = "uploaded_by"


class IsExpiringImageTokenValid(permissions.BasePermission):
    """
    Permission used to check if expiring image token is valid and not expired
    """

    message = "url is invalid or expired"

    def has_permission(self, request: HttpRequest, view: View) -> bool:
        """Check if user has permission to perform request"""

        if not (token := view.kwargs.get("token")) or not (
            path := view.kwargs.get("path")
        ):
            return False

        return expiring_image_token_generator.check_token(path, token)
