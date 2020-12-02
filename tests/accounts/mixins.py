"""
Mixins for setting up test account data in unit tests.

The test data will be initialized ONCE for each test class and
MUST NOT be modified by the tests.

By convention, every password is set to "secret".
"""

from django.contrib.auth import get_user_model

User = get_user_model()


class SimpleAccountsData:
    """Sets up two unprivileged user accounts."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.bob = User.objects.create_user(
            username="bob", email="bob@example.org", password="secret"
        )
        cls.alice = User.objects.create_user(
            username="alice", email="alice@example.org", password="secret"
        )


class AccountsData(SimpleAccountsData):
    """Sets up a superuser, a staff and two unprivileged user accounts."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.chuck = User.objects.create_superuser(
            username="chuck", email="chuck@example.org", password="secret"
        )
        cls.arnold = User.objects.create_user(
            username="arnold", email="arnold@example.org", password="secret", is_staff=True
        )
