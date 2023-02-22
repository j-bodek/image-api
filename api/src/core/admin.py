from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from core.models import User, Tier, ThumbnailSize
from django.utils.translation import gettext_lazy as _


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Class used to register User Admin
    """

    ordering = ["date_joined"]
    list_display = [
        "username",
        "email",
        "tier",
        "last_login_humanize",
        "date_joined_humanize",
    ]
    fieldsets = (
        (
            None,
            {"fields": ("username", "email", "tier")},
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    readonly_fields = ["last_login", "date_joined"]
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "tier",
                    "password1",
                    "password2",
                    "is_active",
                ),
            },
        ),
    )


class ThumbnailSizeInline(admin.StackedInline):
    model = ThumbnailSize
    extra = 1


@admin.register(Tier)
class TierAdmin(admin.ModelAdmin):
    """
    Class used to register tier admin
    """

    ordering = ["id"]
    list_display = ["name"]
    fieldsets = (
        (
            None,
            {"fields": ("name", "has_og_image_access", "can_generate_expire_link")},
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "name",
                    "has_og_image_access",
                    "can_generate_expire_link",
                ),
            },
        ),
    )
    inlines = (ThumbnailSizeInline,)
