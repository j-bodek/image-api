from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import response, status
from rest_framework_simplejwt.tokens import AccessToken
from core.models import Image
from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest import mock
import uuid
import base64


class ViewTestMixin:
    """Provide base setUp method"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="someuser", password="testpassword"
        )
        self.token = AccessToken.for_user(self.user)
        self.client = APIClient()


class TestImageListView(ViewTestMixin, TestCase):
    """Test ImageListView"""

    def test_list_response(self):
        """Test if returned response contain expected data"""

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        r = self.client.get(reverse("images:image_list"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data, [])


class TestImageUploadView(ViewTestMixin, TestCase):
    """Test ImageUploadView"""

    @mock.patch("images.views.image.ImageUploadView.get_serializer")
    def test_if_serializer_save_called(self, mocked_get_serializer):
        """Test if serializer save called with request.user"""

        data = {"uuid": "some_uuid"}
        mockde_serializer = mock.MagicMock(data=data)
        mocked_get_serializer.return_value = mockde_serializer
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        r = self.client.post(
            reverse("images:image_upload"), data={"name": "some_name", "file": bytes()}
        )
        mockde_serializer.save.assert_called_once_with(uploaded_by=self.user)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data, data)


class TestGenerateExpiringImageView(ViewTestMixin, TestCase):
    """Test GenerateExpiringImageView"""

    def setUp(self):
        super().setUp()
        self.image = Image.objects.create(name="someimage", uploaded_by=self.user)

    def create_user(self, **kwargs):
        return get_user_model().objects.create(**kwargs)

    def test_if_not_image_owner(self):
        """should return permission denied"""

        user = self.create_user(username="user", password="testuser")
        token = AccessToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        r = self.client.post(
            reverse("images:image_expiring_create"),
            data={"uuid": str(self.image.uuid), "expire_time": 400},
        )
        self.assertEqual(r.status_code, 403)

    def test_with_not_existing_image_or_image_without_file(self):
        """Should return 404"""

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        send_request = lambda uid: self.client.post(  # noqa
            reverse("images:image_expiring_create"),
            data={"uuid": str(uid), "expire_time": 400},
        )

        for uid in [str(uuid.uuid4()), str(self.image.uuid)]:
            r = send_request(uid)
            self.assertEqual(r.status_code, 404)

    @mock.patch("images.views.image.GenerateExpiringImageView.get_object")
    def teste_with_valid_request(self, mocked_get_object):
        """Should return 200 status code, and data with url, expire time"""

        image = self.image
        image.og_file = mock.MagicMock(name="somefile.jpg")
        mocked_get_object.return_value = image

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        r = self.client.post(
            reverse("images:image_expiring_create"),
            data={"uuid": str(image.uuid), "expire_time": 400},
        )

        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["expire_time"], 400)
        self.assertIn("url", r.data)


class TestExpiringImageView(ViewTestMixin, TestCase):
    """Test ExpiringImageView"""

    def setUp(self):
        super().setUp()
        self.img_token = base64.urlsafe_b64encode("sometoken".encode("utf-8")).decode(
            "utf-8"
        )

    @mock.patch("images.views.image.IsExpiringImageTokenValid.has_permission")
    def test_if_expiring_image_token_valid_called(self, mocked_token_has_permission):
        """Check if IsExpiringImageTokenValid permission is called"""

        mocked_token_has_permission.return_value = False

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        r = self.client.get(
            reverse(
                "images:image_expiring",
                kwargs={"token": self.img_token, "path": "file.jpg"},
            )
        )
        self.assertEqual(r.status_code, 403)
        self.assertEqual(mocked_token_has_permission.call_count, 1)

    @mock.patch("images.views.image.serve")
    @mock.patch("images.views.image.IsExpiringImageTokenValid.has_permission")
    def test_if_serve_called(self, mocked_token_has_permission, mocked_serve):
        """Test if serve called if client has valid permissions"""

        mocked_token_has_permission.return_value = True
        mocked_serve.return_value = response.Response({}, status=status.HTTP_200_OK)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        r = self.client.get(
            reverse(
                "images:image_expiring",
                kwargs={"token": self.img_token, "path": "file.jpg"},
            )
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(mocked_serve.call_count, 1)
