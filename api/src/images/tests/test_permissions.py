from django.test import SimpleTestCase
from unittest import mock
from images import permissions
from core.models import Image
import itertools


class TestIsImageOwnerPermission(SimpleTestCase):
    """Test IsImageOwner permission"""

    def setUp(self):
        self.user = "user"
        self.request = mock.MagicMock(user=self.user)
        self.view = mock.MagicMock()
        self.permission = permissions.IsImageOwner()

    def test_has_object_permission_if_owner(self):
        """has_object_permission should return True"""

        mocked_image = mock.MagicMock(spec=Image, uploaded_by=self.user)
        has_perm = self.permission.has_object_permission(
            request=self.request, view=self.view, obj=mocked_image
        )
        self.assertTrue(has_perm)

    def test_has_object_permission_if_not_owner(self):
        """has_object_permission should return False"""

        mocked_image = mock.MagicMock(spec=Image, uploaded_by="invalid_user")
        has_perm = self.permission.has_object_permission(
            request=self.request, view=self.view, obj=mocked_image
        )
        self.assertFalse(has_perm)


class TestIsExpiringImageTokenValidPermission(SimpleTestCase):
    """Test IsExpiringImageTokenValid permission"""

    def setUp(self):
        self.view = mock.MagicMock()
        self.request = mock.MagicMock()
        self.permission = permissions.IsExpiringImageTokenValid()

    def test_has_permission_without_token_or_path_in_kwargs(self):
        """has_permission should return False"""

        kwargs = {"token": "some_token", "path": "some_path"}
        for i in range(1, len(kwargs)):
            for comb in itertools.combinations(kwargs.items(), i):
                comb = {k: v for k, v in comb}
                self.view.kwargs = comb
                has_perm = self.permission.has_permission(self.request, self.view)
                self.assertFalse(has_perm)

    @mock.patch(
        "images.permissions.expiring_image_token_generator.check_token",
        return_value=False,
    )
    def test_has_permission_with_invalid_token(self, mocked_check_token):
        """has_permission should return False"""

        self.view.kwargs = {"token": "some_token", "path": "some_path"}
        has_perm = self.permission.has_permission(self.request, self.view)
        self.assertEqual(mocked_check_token.call_count, 1)
        self.assertFalse(has_perm)

    @mock.patch(
        "images.permissions.expiring_image_token_generator.check_token",
        return_value=True,
    )
    def test_has_permission_with_valid_token(self, mocked_check_token):
        """has_permission should return True"""

        self.view.kwargs = {"token": "some_token", "path": "some_path"}
        has_perm = self.permission.has_permission(self.request, self.view)
        self.assertEqual(mocked_check_token.call_count, 1)
        self.assertTrue(has_perm)
