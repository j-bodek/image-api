from django.test import SimpleTestCase
from unittest import mock
from images.tokens import expiring_image_token_generator
import base64
import datetime


class TestExpiringImageTokenGenerator(SimpleTestCase):
    """Test ExpiringImageTokenGenerator class"""

    def setUp(self):
        self.token_generator = expiring_image_token_generator

    def test_make_token(self):
        """Test if make token create encrypted urlsafe base64 token"""

        kwargs = {"filename": "somefile.jpg", "expire_time": 400}
        token = self.token_generator.make_token(**kwargs)
        self.assertNotEqual(kwargs.get("filename"), token)
        # check if urlsafe_b64
        base64.urlsafe_b64decode(token.encode()).decode("utf-8")

    def test_check_token_with_valid_token(self):
        """Test if check token return True if token and filename are valid"""

        kwargs = {"filename": "somefile.jpg", "expire_time": 400}
        token = self.token_generator.make_token(**kwargs)
        self.assertTrue(
            self.token_generator.check_token(filename=kwargs["filename"], token=token)
        )

    @mock.patch("images.tokens.ExpiringImageTokenGenerator._get_expire_date")
    def test_check_token_with_invalid_token(self, mocked_expire_date):
        """Test if check_token return False"""

        kwargs = {"filename": "somefile.jpg", "expire_time": 400}
        # test with invalid token
        self.assertFalse(
            self.token_generator.check_token(
                filename=kwargs["filename"], token="invalid_token"
            )
        )

        # test with expired token
        mocked_expire_date.return_value = datetime.datetime.now() - datetime.timedelta(
            seconds=kwargs["expire_time"] + 10
        )
        token = self.token_generator.make_token(**kwargs)
        self.assertFalse(
            self.token_generator.check_token(filename=kwargs["filename"], token=token)
        )
