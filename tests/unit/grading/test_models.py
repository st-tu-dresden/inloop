from django.test import TestCase

from tests.unit.grading.mixins import DetectedPlagiarismData


class GradingModelsTest(DetectedPlagiarismData, TestCase):
    def test_all_detected_plagiarisms_property(self):
        self.assertTrue(
            self.detected_plagiarism_alice
            in self.plagiarism_test.all_detected_plagiarisms
        )
        self.assertTrue(
            self.detected_plagiarism_bob
            in self.plagiarism_test.all_detected_plagiarisms
        )
        self.assertEqual(self.plagiarism_test.all_detected_plagiarisms.count(), 2)
