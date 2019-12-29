from datetime import datetime, timedelta

from django.test import TestCase

from inloop.solutions.statistics import Statistics, date_range_in_between

from tests.solutions.mixins import SolutionsData


class StatisticsTest(SolutionsData, TestCase):
    def setUp(self):
        super().setUp()
        self.statistics_both = Statistics([self.passed_solution, self.failed_solution], '%Y-%m-%d')
        self.statistics_passed_only = Statistics([self.passed_solution], '%Y-%m-%d')
        self.statistics_failed_only = Statistics([self.failed_solution], '%Y-%m-%d')

    def test_single_date_range(self):
        date = datetime.now()
        date_range = date_range_in_between(date, date)
        self.assertEqual(len(date_range), 1)

    def test_date_range(self):
        start_date = datetime.now()
        end_date = start_date + timedelta(days=10)
        test_date = start_date + timedelta(days=3)
        date_range = date_range_in_between(start_date, end_date)
        self.assertEqual(len(date_range), 11)
        self.assertTrue(start_date in date_range)
        self.assertTrue(end_date in date_range)
        self.assertTrue(test_date in date_range)

    def test_statistics_empty_constructor(self):
        msg = 'Error should give a description.'
        with self.assertRaises(ValueError) as context:
            Statistics(solutions=None)
        self.assertTrue(str(context.exception), msg)
        with self.assertRaises(ValueError) as context:
            Statistics(solutions=[])
        self.assertTrue(str(context.exception), msg)

    def test_passed_after(self):
        self.assertEqual(self.statistics_both.passed_after, [(1, 1)])
        self.assertEqual(self.statistics_passed_only.passed_after, [(1, 1)])
        self.assertEqual(self.statistics_failed_only.passed_after, [])

    def test_passed(self):
        self.assertEqual(self.statistics_both.passed, 1)
        self.assertEqual(self.statistics_failed_only.passed, 0)
        self.assertEqual(self.statistics_passed_only.passed, 1)

    def test_failed(self):
        self.assertEqual(self.statistics_both.failed, 1)
        self.assertEqual(self.statistics_failed_only.failed, 1)
        self.assertEqual(self.statistics_passed_only.failed, 0)

    def test_hotspots(self):
        hotspots_b = dict(self.statistics_both.hotspots)
        hotspots_f = dict(self.statistics_failed_only.hotspots)
        hotspots_p = dict(self.statistics_passed_only.hotspots)
        task_title = self.task.title
        self.assertTrue(task_title in hotspots_b)
        self.assertTrue(task_title in hotspots_f)
        self.assertTrue(task_title in hotspots_p)
        value_b = list(hotspots_b.values())[-1]
        self.assertEqual(value_b['passed_submissions'], 1)
        self.assertEqual(value_b['failed_submissions'], 1)
        value_f = list(hotspots_f.values())[-1]
        self.assertEqual(value_f['passed_submissions'], 0)
        self.assertEqual(value_f['failed_submissions'], 1)
        value_p = list(hotspots_p.values())[-1]
        self.assertEqual(value_p['passed_submissions'], 1)
        self.assertEqual(value_p['failed_submissions'], 0)

    def test_submission_dates(self):
        submission_date_failed = self.failed_solution.submission_date
        submission_date_failed_formatted = submission_date_failed.strftime(
            self.statistics_both.date_format
        )
        submission_date_passed = self.passed_solution.submission_date
        submission_date_passed_formatted = submission_date_passed.strftime(
            self.statistics_both.date_format
        )
        if submission_date_passed_formatted == submission_date_failed_formatted:
            self.assertTrue(
                (submission_date_passed_formatted, 2)
                in self.statistics_both.submission_dates
            )
        else:
            self.assertTrue(
                (submission_date_failed_formatted, 1)
                in self.statistics_both.submission_dates
            )
            self.assertTrue(
                (submission_date_passed_formatted, 1)
                in self.statistics_both.submission_dates
            )
