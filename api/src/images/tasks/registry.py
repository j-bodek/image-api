from src import CELERY_APP
from .thumbnails_creator_task import ThumbnailsCreator


thumbnails_creator = CELERY_APP.register_task(ThumbnailsCreator())
