from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.crypto import constant_time_compare, salted_hmac
from django.utils.http import base36_to_int, int_to_base36
import datetime
import base64
import binascii


class ExpiringImageTokenGenerator(PasswordResetTokenGenerator):
    """
    Class used to generate token that gives access to specified image
    for specified amount of time
    """

    def make_token(self, filename: str, expire_time: int) -> str:
        """
        Return a token that can be used multiple time until it expire
        to retrieve image.
        """

        token = self._make_token_with_timestamp(
            filename,
            self._num_seconds(self._get_expire_date(expire_time)),
            self.secret,
        )

        # encode token to base64 safe url format
        return base64.urlsafe_b64encode(token.encode("utf-8")).decode("utf-8")

    def check_token(self, filename: str, token: str) -> bool:
        """
        Check that token is correct and not expired for a given filename
        """

        if not (filename and token):
            return False

        # Parse the token
        try:
            token = base64.urlsafe_b64decode(token.encode()).decode("utf-8")
            ts_b36, _ = token.split("-")
        except (binascii.Error, ValueError):
            return False

        try:
            ts = base36_to_int(ts_b36)
        except ValueError:
            return False

        # Check that the timestamp/uid has not been tampered with
        for secret in [self.secret, *self.secret_fallbacks]:
            if constant_time_compare(
                self._make_token_with_timestamp(filename, ts, secret),
                token,
            ):
                break
        else:
            return False

        # Check if token is not expired
        if (self._num_seconds(self._now()) - ts) > 0:
            return False

        return True

    def _make_token_with_timestamp(
        self, filename: str, timestamp: int, secret: str
    ) -> str:
        """
        Create token based on filename and timestamp
        """

        ts_b36 = int_to_base36(timestamp)
        hash_string = salted_hmac(
            self.key_salt,
            self._make_hash_value(filename, timestamp),
            secret=secret,
            algorithm=self.algorithm,
        ).hexdigest()[
            ::4
        ]  # Limit to shorten the URL.

        return f"{ts_b36}-{hash_string}"

    def _make_hash_value(self, filename: str, timestamp: int) -> str:
        """
        Hash the filename and timestampe
        """

        return f"{filename}{timestamp}"

    def _get_expire_date(self, expire_time: int) -> datetime.datetime:
        """Return date of token expiration"""

        return self._now() + datetime.timedelta(seconds=expire_time)


expiring_image_token_generator = ExpiringImageTokenGenerator()
