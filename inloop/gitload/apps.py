from django.apps import AppConfig


class GitloadAppConfig(AppConfig):
    name = "inloop.gitload"
    verbose_name = "Gitload"

    def ready(self) -> None:
        from . import signals  # noqa
