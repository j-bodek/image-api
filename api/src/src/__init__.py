from __future__ import absolute_import, unicode_literals
from .redis import REDIS
from .celery import app as CELERY_APP

# import redis instance to __init__ file to ensures
# that it will be loaded when django starts
__all__ = ("CELERY_APP", "REDIS")
