from collections import Counter
from http import HTTPStatus

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import functions
from django.http import Http404, HttpRequest, JsonResponse
from django.views import View

from inloop.solutions.models import Solution

from .validators import (get_optional_bool, get_optional_int,
                         get_optional_timestamp, get_optional_truncator_identifier)


def bad_json_request(reason: str = 'Malformed JSON') -> JsonResponse:
    """
    Return a Json Response to indicate a bad json request.

    The returned Json Response has the HTTP response code 403 and
    contains a configurable reason, which can be taken for error handling.
    """
    return JsonResponse({'reason': reason}, status=HTTPStatus.BAD_REQUEST)


def queryset_limit_reached(
    queryset_count: int,
    reason: str = 'Queryset limit reached'
) -> JsonResponse:
    """
    Return a Json Response to indicate, that the queryset limit was reached.

    Depending on the request and the number of objects in the database,
    the number of objects returned in a response can be very big.
    To avoid transmission of a very big number of objects, a view can
    return this response to indicate to the client, that a arbitrary
    object limit was reached, so that the client can react accordingly.
    """
    return JsonResponse({
        'queryset_count': queryset_count,
        'reason': reason
    }, status=HTTPStatus.CONFLICT)


class AdminView(UserPassesTestMixin, LoginRequiredMixin, View):
    """Provide a base view with superuser and staff restricted access."""

    def test_func(self) -> bool:
        """Validate, that the user is logged in as staff or superuser."""
        if not self.request.user:
            raise Http404()
        if not self.request.user.is_superuser and not self.request.user.is_staff:
            raise Http404()
        return True


class SubmissionsHistogramJsonView(AdminView):
    """
    Provide the REST endpoint for the modular submissions histogram.

    The submissions histogram shows submitted solutions
    over a given timespan.
    """

    def get(self, request: HttpRequest) -> JsonResponse:
        """
        Get a filtered solution submission histogram.

        Since the HTTP request type is GET, all parameters must be
        supplied as GET parameters. Validate these parameters first and
        filter the queryset of all solutions based on the parameters.
        Use an SQL truncator to create buckets and
        return a Json Response with the mapped histogram.

        It is possible to pass a queryset limit to
        avoid computation of too many objects.
        """
        try:
            queryset_limit = get_optional_int('queryset_limit', request.GET)
            from_timestamp = get_optional_timestamp('from_timestamp', request.GET)
            to_timestamp = get_optional_timestamp('to_timestamp', request.GET)
            passed = get_optional_bool('passed', request.GET)
            category_id = get_optional_int('category_id', request.GET)
            granularity = get_optional_truncator_identifier('granularity', request.GET)
        except ValidationError as e:
            return bad_json_request(reason=e.message)

        truncator = functions.Trunc('submission_date', granularity)

        queryset = Solution.objects
        if from_timestamp:
            queryset = queryset.filter(submission_date__gte=from_timestamp)
        if to_timestamp:
            queryset = queryset.filter(submission_date__lte=to_timestamp)
        if passed is not None:
            queryset = queryset.filter(passed=passed)
        if category_id is not None:
            queryset = queryset.filter(task__category_id=category_id)

        # Check the queryset count before any expensive ORM computing is done
        queryset_count = queryset.count()
        if queryset_limit is not None and queryset_count > queryset_limit:
            return queryset_limit_reached(queryset_count)

        histogram_queryset = queryset \
            .annotate(date=truncator) \
            .values('date') \
            .annotate(count=models.Count('pk'))

        return JsonResponse({
            'histogram': list(histogram_queryset)
        })


class AttemptsHistogramJsonView(AdminView):
    """
    Provide the REST endpoint for the modular attempts histogram.

    The attempts histogram shows accumulated statistics about
    how many attempts users took for a specific task,
    until they were able to succeed.
    """

    def get(self, request: HttpRequest) -> JsonResponse:
        """
        Get a filtered attempts histogram.

        Since the HTTP request type is GET, all parameters must be
        supplied as GET parameters. Validate these parameters first and
        filter the queryset of all solutions based on the parameters.
        The number of trials until the first passed solution
        is computed through the minimum scoped id of all passed
        solutions for each user. Group these values into buckets
        and return a Json Response with the mapped histogram.

        It is possible to pass a queryset limit to
        avoid computation of too many objects.
        """
        try:
            queryset_limit = get_optional_int('queryset_limit', request.GET)
            task_id = get_optional_int('task_id', request.GET)
        except ValidationError as e:
            return bad_json_request(reason=e.message)
        if task_id is None:
            return bad_json_request(reason='The parameter task_id must be supplied.')

        queryset = Solution.objects \
            .filter(passed=True, task_id=task_id) \
            .values('author_id') \
            .annotate(num_trials=models.Min('scoped_id'))

        # Check the queryset count before any expensive computing is done
        queryset_count = queryset.count()
        if queryset_limit is not None and queryset_count > queryset_limit:
            return queryset_limit_reached(queryset_count)

        histogram = Counter(queryset.values_list('num_trials', flat=True))

        return JsonResponse({
            'histogram': histogram
        })
