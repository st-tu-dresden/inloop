import os
import shutil
from tempfile import mkdtemp

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from inloop.tasks.models import Category

from tests.integration.tools import MessageTestCase
from tests.solutions.mixins import SolutionsData

FIBONACCI = """
public class Fibonacci {
    public static int fib(final int x) {
    if (x < 0) {
        throw new IllegalArgumentException("x must be greater than or equal zero");
    }

    int a = 0;
    int b = 1;

    for (int i = 0; i < x; i++) {
        int sum = a + b;
        a = b;
        b = sum;
    }

    return a;
    }

    /*
     * This string is just here for testing purposes.
     */
}
"""

TEST_MEDIA_ROOT = mkdtemp()


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class SolutionUploadTest(SolutionsData, MessageTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not os.path.isdir(TEST_MEDIA_ROOT):
            os.makedirs(TEST_MEDIA_ROOT)

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.category = Category.objects.create(id=1337, name="Category 1")

    def setUp(self):
        super().setUp()
        self.assertTrue(self.client.login(username="bob", password="secret"))
        self.url = reverse("solutions:upload", kwargs={"slug": self.task.slug})

    def test_solution_upload_without_files(self):
        response = self.client.post(self.url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertResponseContainsMessage(
            "You haven't uploaded any files.",
            self.Levels.ERROR,
            response
        )

    def test_solution_upload_with_multiple_files(self):
        file_1 = SimpleUploadedFile("Fibonacci1.java", "class Fibonacci1 {}".encode())
        file_2 = SimpleUploadedFile("Fibonacci2.java", "class Fibonacci2 {}".encode())
        response = self.client.post(self.url, data={
            "uploads": [file_1, file_2]
        }, follow=True)
        self.assertResponseContainsMessage(
            "Your solution has been submitted to the checker.",
            self.Levels.SUCCESS,
            response
        )
        # Extract all files in media root
        file_names = [
            item for sublist in list(l for _, _, l in os.walk(TEST_MEDIA_ROOT))
            for item in sublist
        ]
        self.assertIn("Fibonacci1.java", file_names)
        self.assertIn("Fibonacci2.java", file_names)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_MEDIA_ROOT)
        super().tearDownClass()
