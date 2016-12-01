from django.utils import timezone

from inloop.tasks.models import Category, Task


class CategoryData:
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.category1 = Category.objects.create(name="Category 1")
        cls.category2 = Category.objects.create(name="Category 2")


class TaskData(CategoryData):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.published_task1 = Task.objects.create(
            title="Task 1",
            category=cls.category1,
            description="Task 1 description",
            system_name="Task1",
            pubdate=timezone.now(),
            slug="task-1"
        )
        cls.published_task2 = Task.objects.create(
            title="Task 2",
            category=cls.category1,
            description="Task 2 description",
            system_name="Task2",
            pubdate=timezone.now(),
            slug="task-2"
        )
        cls.unpublished_task1 = Task.objects.create(
            title="Unpublished Task 1",
            category=cls.category1,
            description="Unpublished Task 1 description",
            system_name="UnpublishedTask1",
            pubdate=timezone.now() + timezone.timedelta(days=7),
            slug="unpublished-task-1"
        )
        cls.unpublished_task2 = Task.objects.create(
            title="Unpublished Task 2",
            category=cls.category1,
            description="Unpublished Task 2 description",
            system_name="UnpublishedTask2",
            pubdate=timezone.now() + timezone.timedelta(days=7),
            slug="unpublished-task-2"
        )
