from unittest.mock import patch
from psycopg2 import OperationalError as Psycopg2OperationalError
from django.db.utils import OperationalError
from django.test import SimpleTestCase
from django.core.management import call_command


# mock wait_for_db command check method
@patch("core.management.commands.wait_for_db.Command.check")
class TestWaitForDatabaseCommand(SimpleTestCase):
    """
    Test if wait_for_db command works properly
    """

    # patched_check argument is returned by unittest patch
    def test_wait_for_db_if_ready(self, patched_check):
        """
        Test if command check database once if it is ready
        """

        patched_check.return_value = True
        call_command("wait_for_db")

        # check if patched_check method was called once with databases
        # kwarg = ["default"]
        patched_check.assert_called_once_with(databases=["default"])

    # patch sleep method
    @patch("time.sleep")
    def test_wait_for_db_dont_ready(self, patched_time, patched_check):
        """
        Test if command wait in case database is not ready
        """

        # list of values that will be returned when patched_check is called
        # one at a time
        patched_check.side_effect = [
            Psycopg2OperationalError,
            OperationalError,
            True,
        ]
        call_command("wait_for_db")
        self.assertEqual(patched_check.call_count, 3)
        patched_check.assert_called_with(databases=["default"])
