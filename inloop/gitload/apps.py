from django.apps import AppConfig


class GitloadAppConfig(AppConfig):
    name = "inloop.gitload"
    verbose_name = "Gitload"

    def ready(self):
        from . import signals  # noqa
