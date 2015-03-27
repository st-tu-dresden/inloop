from django.db import models
from django.contrib.auth import models as auth_models
from accounts.validators import validate_mat_num


class CourseOfStudy(models.Model):
    '''
    Represents the course of study of the
    respective user.
    '''
    name = models.CharField(
        max_length=50,
        help_text='The course name',
        unique=True)

    def __str__(self):
        return self.name


class UserProfile(auth_models.AbstractUser):
    '''
    Basic user. Already set (min 30 chars):
    Username, First Name, Last Name, E-Mail
    '''

    mat_num = models.IntegerField(
        max_length=7,
        help_text='Matriculation Number',
        null=True,
        validators=[validate_mat_num]
    )
    course = models.ForeignKey(CourseOfStudy, null=True)
