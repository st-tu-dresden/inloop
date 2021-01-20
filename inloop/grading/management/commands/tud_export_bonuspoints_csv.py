import csv
from datetime import datetime
from typing import Any, Iterable, Iterator, Tuple

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandParser

from inloop.grading.tud import calculate_grades, points_for_completed_tasks

User = get_user_model()


def filter_zeroes(grade_seq: Iterable[Tuple]) -> Iterator[Any]:
    """Filter grade rows where the last item equals zero."""
    return (x for x in grade_seq if x[-1] != 0)


class Command(BaseCommand):
    help = "Write a CSV sheet with points based on completed tasks in a category."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("category_name", help="Name of the category to base points on")
        parser.add_argument("start_date", help="Start date for considered solutions (YYYY-mm-dd)")
        parser.add_argument("csv_file", help="File to write the CSV sheet to")
        parser.add_argument("--zeroes", help="Include zero point entries", action="store_true")

    def handle(self, *args: str, **options: Any) -> None:
        start_date = datetime.strptime(options["start_date"], "%Y-%m-%d")
        self.stdout.write(f"Evaluating bonus points for solutions after {start_date}")

        users = User.objects.filter(is_staff=False)
        gradefunc = points_for_completed_tasks(options["category_name"], start_date, 10)
        grades = calculate_grades(users, gradefunc)

        if not options["zeroes"]:
            grades = filter_zeroes(grades)

        # we guessed some names and can't sort at the database layer
        grades = list(grades)
        grades.sort()

        with open(options["csv_file"], mode="w", newline="") as csv_file:
            writer = csv.writer(csv_file)
            for row in grades:
                writer.writerow(row)

        self.stdout.write(self.style.SUCCESS("Successfully created %s" % options["csv_file"]))
