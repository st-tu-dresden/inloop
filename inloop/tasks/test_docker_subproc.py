from os.path import dirname, join

from django.test import TestCase

from inloop.tasks.docker import collect_files


class CollectorTest(TestCase):
    test_harness = join(dirname(__file__), "tests/file_dict")

    def test_collected_names(self):
        filenames = collect_files(self.test_harness).keys()
        self.assertEqual(len(filenames), 2)
        self.assertIn("empty1.txt", filenames)
        self.assertIn("README.md", filenames)
        self.assertNotIn("should_be_ignored", filenames)
        self.assertNotIn("empty2.txt", filenames)

    def test_collected_contents(self):
        file_dict = collect_files(self.test_harness)
        self.assertEqual("", file_dict["empty1.txt"])
        self.assertEqual("This is a test harness for collect_files().\n", file_dict["README.md"])
