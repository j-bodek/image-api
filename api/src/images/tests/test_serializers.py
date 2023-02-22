from django.test import SimpleTestCase, TestCase
from rest_framework.exceptions import ValidationError, NotFound
from images.serializers.image import ExpiringImageSerializer, ImageCreateSerializer
from django.core.management import call_command
from core.models import Tier, Image
from django.urls import reverse
from unittest import mock
import base64


class TestExpiringImageSerializer(SimpleTestCase):
    """Test ExpiringImageSerializer"""

    def setUp(self):
        self.serializer_class = ExpiringImageSerializer
        self.token = base64.urlsafe_b64encode("sometoken".encode("utf-8")).decode(
            "utf-8"
        )

    def test_validate_expire_time(self):
        """Test if raises ValidationError if expire_time not in range [300, 30000]"""

        serializer = self.serializer_class()
        valid_values = [300, 30000, 500, 1000]
        for value in valid_values:
            self.assertEqual(value, serializer.validate_expire_time(value))

        invalid_values = [-100, 299, 30001, 100000]
        for value in invalid_values:
            with self.assertRaises(ValidationError):
                serializer.validate_expire_time(value)

    def test_generate_expire_img_url_without_request(self):
        """Test generate_expire_img_url if request is not in context.
        Relative path should be returned"""

        serializer = self.serializer_class()
        kwargs = {"token": self.token, "path": "file.jpg"}

        self.assertEqual(
            reverse("images:image_expiring", kwargs=kwargs),
            serializer.generate_expire_img_url(kwargs["token"], kwargs["path"]),
        )

    def test_generate_expire_img_url_with_request(self):
        """Test generate_expire_img_url if request is in context.
        Absolute url should be returned"""

        mocked_request = mock.MagicMock()
        mocked_request.build_absolute_uri = lambda url: f"http://example{url}"

        serializer = self.serializer_class(context={"request": mocked_request})
        kwargs = {"token": self.token, "path": "file.jpg"}

        self.assertEqual(
            "http://example" + reverse("images:image_expiring", kwargs=kwargs),
            serializer.generate_expire_img_url(kwargs["token"], kwargs["path"]),
        )

    def test_create_expiring_img_link_without_og_file(self):
        """Test create_expiring_img_link for Image without og_file. NotFound
        should be raised"""

        serializer = self.serializer_class()
        with self.assertRaises(NotFound):
            serializer.create_expiring_img_link(image=mock.MagicMock(og_file=None))

    def create_expiring_img_link_with_og_file(self):
        """Test create_expiring_img_link for Image with og_file.
        _validated_data should be updated with generated url"""

        image = mock.MagicMock(og_file=mock.MagicMock(name="file.jpg"))
        serializer = self.serializer_class()
        serializer._validated_data = {"expire_time": 400}
        serializer.expiring_image_token_generator = mock.MagicMock(
            make_token=lambda filename, expire_time: self.token
        )
        serializer.create_expiring_img_link(image=image)
        self.assertIn(self.token, serializer._validated_data["url"])
        self.assertTrue(serializer._validated_data["url"].endswith("file.jpg"))


class TestImageCreateSerializer(TestCase):
    """Test ImageCreateSerializer"""

    def setUp(self):
        self.serializer_class = ImageCreateSerializer
        call_command("loaddata", "tiers")
        self.tier_thumbnails_data = {
            "Basic": [[None, 200]],
            "Premium": [[None, 200], [None, 400]],
            "Enterprise": [[None, 200], [None, 400]],
        }

    @mock.patch("images.serializers.image.models.Thumbnail.generate_absolute_url")
    def test_get_thumbnails(self, mocked_abs_url_generator):
        """list of dicts with thumbnails data should be returned
        (if thumbnails in validated data)"""

        serializer = self.serializer_class(context={"request": mock.MagicMock()})
        # check if return emtpy generator
        for obj in [None, mock.MagicMock()]:
            thumbnails = serializer.get_thumbnails(obj=obj)
            self.assertEqual(list(thumbnails), [])

        # check if return expected data
        serializer._validated_data = {
            "thumbnails": [{"height": 200, "width": 200, "file": "somefile"}]
        }
        mocked_abs_url_generator.return_value = "abs_url"
        thumbnails = serializer.get_thumbnails(obj=mock.MagicMock())
        self.assertEqual(
            list(thumbnails), [{"height": 200, "width": 200, "file": "abs_url"}]
        )

    def test_get_thumbnails_data(self):
        """Should return list of thumbnails data for specified user"""
        serializer = self.serializer_class()
        for tier in Tier.objects.all():
            user = mock.MagicMock(tier=tier)
            for thumbnail in serializer.get_thumbnails_data(
                user=user, extension=".jpeg"
            ):
                size = [thumbnail["width"], thumbnail["height"]]
                self.assertIn(size, self.tier_thumbnails_data[tier.name])

    @mock.patch("images.serializers.image.REDIS")
    @mock.patch("images.serializers.image.thumbnails_creator")
    @mock.patch("images.serializers.image.serializers.ModelSerializer.create")
    def test_create(self, mocked_super_create, mocked_thumbnails_creator, mocked_redis):
        """Should create Image object, cache image in redis, and delay
        thumbnails_creator celery task"""

        mocked_instance = mock.MagicMock(spec=Image)
        mocked_super_create.return_value = mocked_instance
        user = mock.MagicMock(tier=Tier.objects.get(name="Basic"))
        serializer = self.serializer_class(
            context={"request": mock.MagicMock(user=user)}
        )
        serializer._validated_data = {}
        instance = serializer.create(
            validated_data={"og_file": mock.MagicMock(name="somefile.jpg")}
        )
        # check if redis and celery called
        self.assertEqual(mocked_redis.set.call_count, 1)
        self.assertEqual(mocked_thumbnails_creator.delay.call_count, 1)
        # check instance and validated data
        self.assertEqual(instance, mocked_instance)
        self.assertNotEqual(serializer._validated_data.get("thumbnails"), None)
