from django.dispatch import Signal, receiver

from constance import config
from constance.signals import config_updated

repository_loaded = Signal(providing_args=['repository'])


@receiver(config_updated, dispatch_uid='gitload_config_updated')
def handle_config_updated(sender, key, **kwargs):
    if key in ['GITLOAD_URL', 'GITLOAD_BRANCH']:
        if config.GITLOAD_URL and config.GITLOAD_BRANCH:
            from inloop.gitload.tasks import load_tasks_async
            load_tasks_async()
