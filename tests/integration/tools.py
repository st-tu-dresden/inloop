from django.contrib.messages import get_messages
from django.test import TestCase


class MessageTestCase(TestCase):
    """Supply basic assertions for the Django Messages framework."""

    class Levels:
        DEBUG = 10
        INFO = 20
        SUCCESS = 25
        WARNING = 30
        ERROR = 40

    def assertResponseContainsMessage(self, text, level, response, msg=None):
        messages = list(get_messages(response.wsgi_request))
        for message in messages:
            if message.message == text and message.level == level:
                return
        msg = self._formatMessage(
            msg,
            'The given response did not contain a message '
            'with text "{}" and level "{}"'.format(text, level)
        )
        raise self.failureException(msg)
