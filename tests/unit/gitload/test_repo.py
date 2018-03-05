from unittest import TestCase

from inloop.gitload.repo import Repository

from . import TESTREPO_PATH


class RepositoryTest(TestCase):
    def setUp(self):
        self.repo = Repository(TESTREPO_PATH)

    def test_find_files(self):
        self.assertEquals(5, len(list(self.repo.find_files("*/task.md"))))
        self.assertEquals(4, len(list(self.repo.find_files("*/meta.json"))))

    def test_repo_path(self):
        self.assertEqual("testrepo", self.repo.path.name)
