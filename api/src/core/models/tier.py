from django.db import models
from django.utils.translation import gettext_lazy as _


class Tier(models.Model):
    """
    Model that allow to create user tier
    """

    name = models.CharField(max_length=255, unique=True, null=False, blank=False)
    has_og_image_access = models.BooleanField(
        default=False,
        help_text="Specify whether user can access original size image",
    )
    can_generate_expire_link = models.BooleanField(
        default=False,
        help_text="Specify whether user can generate expiring image links",
    )

    class Meta:
        verbose_name = _("tier")
        verbose_name_plural = _("tiers")

    def __str__(self) -> str:
        """Return string representation of Tier instance"""
        return str(self.name)


class ThumbnailSize(models.Model):
    """
    Model used to define allowed thumbnail sizes for
    specified tier
    """

    tier = models.ForeignKey(
        Tier, null=False, blank=False, on_delete=models.CASCADE, related_name="sizes"
    )
    height = models.IntegerField(null=True, blank=True)
    width = models.IntegerField(null=True, blank=True)
