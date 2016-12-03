from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models


class Course(models.Model):
    """Course of study."""

    name = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return self.name


def default_course():
    course, _ = Course.objects.get_or_create(name="Other")
    return course.id


class StudentDetails(models.Model):
    """Associate additional data to the user account."""

    class Meta:
        verbose_name_plural = "Student details"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    matnum = models.CharField(blank=True, max_length=20, validators=[
        RegexValidator(r'^[0-9]*$', "Please enter a numeric value or leave the field blank.")
    ])
    course = models.ForeignKey(Course, default=default_course, on_delete=models.PROTECT)

    def __str__(self):
        return str(self.user)
