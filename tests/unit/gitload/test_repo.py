from unittest import TestCase

from inloop.gitload.repo import GitRepository, Repository

from . import TESTREPO_PATH


class RepositoryTest(TestCase):
    def setUp(self):
        self.repo = Repository(TESTREPO_PATH)

    def test_find_files(self):
        self.assertEquals(5, len(list(self.repo.find_files("*/task.md"))))
        self.assertEquals(4, len(list(self.repo.find_files("*/meta.json"))))

    def test_repo_path_and_path_s(self):
        self.assertEqual("testrepo", self.repo.path.name)
        self.assertTrue(self.repo.path_s.endswith("testrepo"))

    def test_repr(self):
        self.assertRegex(repr(self.repo), r"Repository\('.*testrepo.*'\)")


class ArgumentCheckTest(TestCase):
    def test_empty_path_raises_valueerror(self):
        with self.assertRaisesRegex(ValueError, "path must not be empty"):
            Repository("")

    def test_empty_url_raises_valueerror(self):
        with self.assertRaisesRegex(ValueError, "url must not be empty"):
            GitRepository("foo", url="", branch="master")

    def test_empty_branch_raises_valueerror(self):
        with self.assertRaisesRegex(ValueError, "branch must not be empty"):
            GitRepository("foo", url="file:///path/to/repo", branch="")
