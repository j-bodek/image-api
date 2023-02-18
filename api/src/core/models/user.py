from django.contrib.auth.models import (
    AbstractUser,
)
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.humanize.templatetags import humanize


class User(AbstractUser):
    """
    Custom user model that extends basic django User model
    with tiers
    """

    uuid = models.UUIDField(
        primary_key=True,
        editable=False,
        default=uuid.uuid4,
        max_length=36,
    )

    tier = models.ForeignKey(
        "core.Tier",
        verbose_name=_("tier"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        help_text=_("The tier this user belongs to."),
    )

    @property
    def last_login_humanize(self) -> str:
        """returns humanized last login date"""

        return humanize.naturaltime(self.last_login)

    @property
    def date_joined_humanize(self) -> str:
        """returns humanized join date"""

        return humanize.naturaltime(self.date_joined)
