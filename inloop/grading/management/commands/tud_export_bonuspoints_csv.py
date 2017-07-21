import csv
from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from inloop.grading.tud import calculate_grades, points_for_completed_tasks

User = get_user_model()


class Command(BaseCommand):
    help = "Write a CSV sheet with points based on completed tasks in a category."

    def add_arguments(self, parser):
        parser.add_argument("category_name", help="Name of the category to base points on")
        parser.add_argument("start_date", help="Start date for considered solutions")
        parser.add_argument("csv_file", help="File to write the CSV sheet to")

    def handle(self, *args, **options):
        start_date = datetime.strptime(options["start_date"], "%Y-%m-%d")
        users = User.objects.filter(is_staff=False)
        gradefunc = points_for_completed_tasks(options["category_name"], start_date, 10)

        self.stdout.write("Evaluating bonus points for solutions after %s" % start_date)

        with open(options["csv_file"], mode="w", newline="") as csv_file:
            writer = csv.writer(csv_file)
            for row in calculate_grades(users, gradefunc):
                writer.writerow(row)

        self.stdout.write(self.style.SUCCESS("Successfully created %s" % options["csv_file"]))
