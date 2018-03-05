from django.apps import AppConfig


class TestRunnerConfig(AppConfig):
    name = "inloop.testrunner"
    verbose_name = "Test runner"

    def ready(self):
        from . import signals   # noqa
