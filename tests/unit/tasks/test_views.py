from django.utils.encoding import force_text

from tests.unit.tasks.test_base import TasksTestBase


class SolutionStatusViewTest(TasksTestBase):
    def setUp(self):
        super().setUp()
        self.another_user = self.create_user("Bruce Lee")
        self.solution = self.create_solution()

    def test_pending_state(self):
        self.client.login(username="chuck_norris", password="s3cret")
        response = self.client.get("/tasks/solution/%d/status" % self.solution.id)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_text(response.content),
            '{"status": "pending", "solution_id": %d}' % self.solution.id
        )

    def test_only_owner_can_access(self):
        self.client.login(username="bruce_lee", password="s3cret")
        response = self.client.get("/tasks/solution/%d/status" % self.solution.id)
        self.assertEqual(response.status_code, 404)
