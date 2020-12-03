import logging

from huey import crontab
from huey.contrib.djhuey import db_periodic_task

from inloop.accounts.models import prune_invalid_users

logger = logging.getLogger(__name__)


@db_periodic_task(crontab(minute="*/30"))
def autoprune_invalid_users() -> None:
    num_deleted = prune_invalid_users()
    logger.info(f"Pruned {num_deleted} invalid account(s).")
