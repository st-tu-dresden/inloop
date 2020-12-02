from datetime import datetime

from django.test import RequestFactory, TestCase
from django.utils.timezone import make_aware

from inloop.solutions.admin import SemesterListFilter, SolutionAdmin
from inloop.solutions.models import Solution

from tests.accounts.mixins import AccountsData
from tests.tasks.mixins import TaskData


class SemesterListFilterTest(AccountsData, TaskData, TestCase):
    def setUp(self):
        self.requests = RequestFactory()
        self.solution1 = Solution.objects.create(author=self.alice, task=self.published_task1)
        self.solution1.submission_date = make_aware(datetime(2020, 3, 31))
        self.solution1.save()
        self.solution2 = Solution.objects.create(author=self.alice, task=self.published_task1)
        self.solution2.submission_date = make_aware(datetime(2020, 4, 1))
        self.solution2.save()

    def test_no_choices_when_no_solutions(self):
        Solution.objects.all().delete()
        request = self.requests.get("/", {})
        list_filter = SemesterListFilter(request, {}, Solution, SolutionAdmin)
        self.assertEqual([], list_filter.lookups(request, SolutionAdmin))

    def test_choices_with_solution(self):
        request = self.requests.get("/", {})
        list_filter = SemesterListFilter(request, {}, Solution, SolutionAdmin)
        expected = [
            ("2019s", "Summer 2019"),
            ("2019w", "Winter 2019/2020"),
            ("2020s", "Summer 2020"),
            ("2020w", "Winter 2020/2021"),
        ]
        self.assertEqual(expected, list_filter.lookups(request, SolutionAdmin))

    def test_param_gets_parsed(self):
        params = {"semester": "2020s"}
        request = self.requests.get("/", params)
        list_filter = SemesterListFilter(request, params, Solution, SolutionAdmin)
        self.assertEqual("2020s", list_filter.value())

    def test_filter_winter_semester(self):
        params = {"semester": "2019w"}
        request = self.requests.get("/", params)
        list_filter = SemesterListFilter(request, params, Solution, SolutionAdmin)
        queryset = list_filter.queryset(request, Solution.objects.all())
        self.assertEqual(list(queryset), [self.solution1])

    def test_filter_summer_semester(self):
        params = {"semester": "2020s"}
        request = self.requests.get("/", params)
        list_filter = SemesterListFilter(request, params, Solution, SolutionAdmin)
        queryset = list_filter.queryset(request, Solution.objects.all())
        self.assertEqual(list(queryset), [self.solution2])

    def test_no_filter_when_param_is_invalid1(self):
        params = {"semester": "not-a-number"}
        request = self.requests.get("/", params)
        list_filter = SemesterListFilter(request, params, Solution, SolutionAdmin)
        queryset = list_filter.queryset(request, Solution.objects.all())
        self.assertEqual(list(queryset), [self.solution1, self.solution2])

    def test_no_filter_when_param_is_invalid2(self):
        params = {"semester": "2020a"}
        request = self.requests.get("/", params)
        list_filter = SemesterListFilter(request, params, Solution, SolutionAdmin)
        queryset = list_filter.queryset(request, Solution.objects.all())
        self.assertEqual(list(queryset), [self.solution1, self.solution2])

    def test_no_filter_when_param_is_missing(self):
        request = self.requests.get("/", {})
        list_filter = SemesterListFilter(request, {}, Solution, SolutionAdmin)
        queryset = list_filter.queryset(request, Solution.objects.all())
        self.assertEqual(list(queryset), [self.solution1, self.solution2])
