from django.test import TestCase
from django.utils.encoding import force_text

from inloop.solutions.models import Solution

from tests.accounts.mixins import SimpleAccountsData
from tests.tasks.mixins import TaskData


class SolutionStatusViewTest(TaskData, SimpleAccountsData, TestCase):
    def setUp(self):
        self.solution = Solution.objects.create(author=self.bob, task=self.published_task1)

    def test_pending_state(self):
        self.assertTrue(self.client.login(username="bob", password="secret"))
        response = self.client.get("/solutions/%d/status" % self.solution.id)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_text(response.content),
            '{"status": "pending", "solution_id": %d}' % self.solution.id
        )

    def test_only_owner_can_access(self):
        self.assertTrue(self.client.login(username="alice", password="secret"))
        response = self.client.get("/solutions/%d/status" % self.solution.id)
        self.assertEqual(response.status_code, 404)
