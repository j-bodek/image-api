from django.core.management import BaseCommand
from django.db.utils import OperationalError
from psycopg2 import OperationalError as Psycopg2OperationalError
import time


class Command(BaseCommand):
    """
    This command is used to check if database service
    is running. It allows to eliminate database race condition.
    Race conditions in docker are described here
    https://www.blog.labouardy.com/preventing-race-conditions-in-docker/
    """

    def handle(self, *args, **kwargs) -> None:
        self.stdout.write("Waiting for db")
        db_ready = False
        while db_ready is False:
            try:
                # check database status by trying to connect
                self.check(databases=["default"])
                # if successfully connected set db_ready to True
                db_ready = True
            except (Psycopg2OperationalError, OperationalError):
                self.stdout.write("Database not ready yet")
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS("Database ready"))
