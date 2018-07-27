from collections import defaultdict
from datetime import datetime, timedelta
from itertools import groupby


class Statistics:
    def __init__(self, solutions, date_format="%Y-%m-%d"):
        if not solutions:
            raise ValueError("Solutions should not be empty!")
        self.solutions = solutions
        self.date_format = date_format

    @property
    def passed(self):
        """Calculate how many solutions were passed."""
        return len([s for s in self.solutions if s.passed])

    @property
    def failed(self):
        """Calculate how many solutions failed."""
        return len([s for s in self.solutions if not s.passed])

    @property
    def submission_dates(self):
        """
        Create data for the "submission date" chart.

        The "submission date" chart shows the selected submissions over time.
        """
        all_dates = [s.submission_date.date() for s in self.solutions]
        if not all_dates:
            return []
        all_dates.sort()
        # Add all dates in the range between least recent and most recent
        date_range = date_range_in_between(all_dates[0], all_dates[-1])
        all_dates += date_range
        # Group dates by day
        dates_grouped = groupby(all_dates, key=datetime.toordinal)
        # Assign dates to their occurrences in the data
        # It is important that we subtract 1 from the occurrences
        # since we added 1 by adding every date in the date span
        dates = [(datetime.fromordinal(k).strftime(self.date_format), len(list(v)) - 1)
                 for k, v in dates_grouped]
        return dates

    @property
    def passed_after(self):
        """
        Create data for the "passed after" chart.

        The "passed after" chart asserts when a user statistically
        passes a task.
        """
        # Iterate over all solutions and remember the
        # first passed solution by an author
        solutions_after = []
        tasks_to_authors = []
        for solution in self.solutions:
            if not solution.passed:
                continue
            task_to_author = (solution.task_id, solution.author_id)
            if task_to_author not in tasks_to_authors:
                tasks_to_authors.append(task_to_author)
                solutions_after.append(solution.scoped_id)
        passed_after = [(key, len(list(group))) for key, group in groupby(solutions_after)]
        passed_after.sort(key=lambda x: x[0])
        return passed_after

    @property
    def hotspots(self):
        """
        Create data for the "hotspot" chart.

        The "hotspot" chart shows the selected tasks based on their
        popularity, using a two dimensional point chart with the following
        information per data point:

            - Passed solutions in total
            - Failed solutions in total

        Return the dictionary holding tasks by passed and failed solutions.
        """
        hotspot_tasks = defaultdict(lambda: defaultdict(int))
        for solution in self.solutions:
            if solution.passed:
                hotspot_tasks[solution.task.title]['passed_submissions'] += 1
            else:
                hotspot_tasks[solution.task.title]['failed_submissions'] += 1
        return hotspot_tasks.items()


def date_range_in_between(start_date, end_date):
    """Create a list of dates in between a start and end date."""
    return [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]
